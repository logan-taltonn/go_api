// toy rest go api with sql, mux, & redis
package main

import (
	"bufio"
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/go-redis/redis/v8"
	_ "github.com/go-sql-driver/mysql"
	"github.com/gorilla/mux"
)

var db *sql.DB
var err error
var redisClient *redis.Client
var cacheExpiration time.Duration

type ProfResp struct {
	ClassID       string  `json:"class_id"`
	Semester      string  `json:"sem"`
	SectionNumber int     `json:"section_number"`
	Acnt          int     `json:"a_cnt"`
	Aperc         float32 `json:"a_perc"`
	Bcnt          int     `json:"b_cnt"`
	Bperc         float32 `json:"b_perc"`
	Ccnt          int     `json:"c_cnt"`
	Cperc         float32 `json:"c_perc"`
	Dcnt          int     `json:"d_cnt"`
	Dperc         float32 `json:"d_perc"`
	Fcnt          int     `json:"f_cnt"`
	Fperc         float32 `json:"f_perc"`
	Af            int     `json:"af"`
	Gpa           float32 `json:"gpa"`
	I             int     `json:"i"`
	S             int     `json:"s"`
	U             int     `json:"u"`
	Q             int     `json:"q"`
	X             int     `json:"x"`
	Total         int     `json:"total"`
}

type ClassResp struct {
	Semester      string  `json:"sem"`
	SectionNumber int     `json:"section_number"`
	Acnt          int     `json:"a_cnt"`
	Aperc         float32 `json:"a_perc"`
	Bcnt          int     `json:"b_cnt"`
	Bperc         float32 `json:"b_perc"`
	Ccnt          int     `json:"c_cnt"`
	Cperc         float32 `json:"c_perc"`
	Dcnt          int     `json:"d_cnt"`
	Dperc         float32 `json:"d_perc"`
	Fcnt          int     `json:"f_cnt"`
	Fperc         float32 `json:"f_perc"`
	Af            int     `json:"af"`
	Gpa           float32 `json:"gpa"`
	I             int     `json:"i"`
	S             int     `json:"s"`
	U             int     `json:"u"`
	Q             int     `json:"q"`
	X             int     `json:"x"`
	Total         int     `json:"total"`
	ProfessorName string  `json:"professor_name"`
}

// redis cache startup
func createRedisClient() *redis.Client {
	client := redis.NewClient(&redis.Options{
		Addr:     "localhost:6379",
		Password: "",
		DB:       0,
	})
	return client
}

// get all grades for a particular class
// postman ex: http://localhost:8000/grades/cl?class_name=CSCE-121
func getGradesForClass(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	className := r.URL.Query().Get("class_name")

	// check if data alr in cache
	cachedData, err := redisClient.Get(context.Background(), className).Result()
	if err == nil {
		w.Write([]byte(cachedData))
		return
	}

	// conv sql query into string
	file, err := os.Open("sql/search_class.sql")
	if err != nil {
		panic(err)
	}
	defer file.Close()
	queryBytes, err := io.ReadAll(file)
	if err != nil {
		panic(err)
	}
	query := string(queryBytes)

	// execute query
	res, err := db.Query(query, className)
	if err != nil {
		panic(err.Error())
	}
	defer res.Close()

	// format json via struct model
	var resps []ClassResp
	for res.Next() {
		var resp ClassResp
		err := res.Scan(&resp.Semester, &resp.SectionNumber, &resp.Acnt, &resp.Aperc, &resp.Bcnt, &resp.Bperc, &resp.Ccnt, &resp.Cperc, &resp.Dcnt, &resp.Dperc, &resp.Fcnt, &resp.Fperc, &resp.Af, &resp.Gpa, &resp.I, &resp.S, &resp.U, &resp.Q, &resp.X, &resp.Total, &resp.ProfessorName)
		if err != nil {
			panic(err.Error())
		}
		resps = append(resps, resp)
	}

	// cache the data into redis
	jsonData, err := json.Marshal(resps)
	if err != nil {
		panic(err.Error())
	}
	err = redisClient.Set(context.Background(), className, jsonData, cacheExpiration).Err()
	if err != nil {
		panic(err.Error()) // maybe panic in another way?
	}

	// write to resp writer
	w.Write(jsonData)
}

// get all grades for a partilcular prof
// postman ex: http://localhost:8000/grades/pr?prof_name=TYAGI A
func getGradesForProf(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	profName := r.URL.Query().Get("prof_name")

	// check if data alr in cache
	cachedData, err := redisClient.Get(context.Background(), profName).Result()
	if err == nil {
		w.Write([]byte(cachedData))
		return
	}

	// conv sql query into string
	file, err := os.Open("sql/search_prof.sql")
	if err != nil {
		panic(err)
	}
	defer file.Close()
	queryBytes, err := io.ReadAll(file)
	if err != nil {
		panic(err)
	}
	query := string(queryBytes)

	// execute query
	res, err := db.Query(query, profName)
	if err != nil {
		panic(err.Error())
	}
	defer res.Close()

	// format json via struct model
	var resps []ProfResp
	for res.Next() {
		var resp ProfResp
		err := res.Scan(&resp.ClassID, &resp.Semester, &resp.SectionNumber, &resp.Acnt, &resp.Aperc, &resp.Bcnt, &resp.Bperc, &resp.Ccnt, &resp.Cperc, &resp.Dcnt, &resp.Dperc, &resp.Fcnt, &resp.Fperc, &resp.Af, &resp.Gpa, &resp.I, &resp.S, &resp.U, &resp.Q, &resp.X, &resp.Total)
		if err != nil {
			panic(err.Error())
		}
		resps = append(resps, resp)
	}

	// cache the data into redis
	jsonData, err := json.Marshal(resps)
	if err != nil {
		panic(err.Error())
	}
	err = redisClient.Set(context.Background(), profName, jsonData, cacheExpiration).Err()
	if err != nil {
		panic(err.Error())
	}

	// write to resp writer
	w.Write(jsonData)
}

func main() {
	// startup connection to local mysql
	fmt.Println("starting up rest api...")
	defer fmt.Println("shutting down rest api...")
	db, err = sql.Open("mysql", "logan:@tcp(127.0.0.1:3306)/db")
	if err != nil {
		log.Fatal(err)
		panic(err.Error())
	}
	defer db.Close()

	// ping mysql db to check the connection
	err = db.Ping()
	if err != nil {
		log.Fatal("failed to connect to db:", err)
	}
	fmt.Println("connection to db is successful...")

	// startup redis cache, user input for expiration
	redisClient = createRedisClient()
	reader := bufio.NewReader(os.Stdin)
	fmt.Print("enter cache expiration time in minutes: ")
	input, _ := reader.ReadString('\n')
	usrExpir, err := strconv.Atoi(strings.TrimSpace(input))
	if err != nil {
		fmt.Println("invalid input, setting to default 30min cache...")
		cacheExpiration = 30 * time.Minute
	} else {
		cacheExpiration = time.Duration(usrExpir) * time.Minute
	}

	// startup api listening
	fmt.Println("you may now query...")
	r := mux.NewRouter()
	r.HandleFunc("/grades/cl", getGradesForClass).Methods("GET")
	r.HandleFunc("/grades/pr", getGradesForProf).Methods("GET")
	log.Fatal(http.ListenAndServe(":8000", r))
}
