import re
import PyPDF2
import mysql.connector

# --- create db & tables -----------------------------------------------------------------------------------------------------------------------------------------------
db_config = {
    "host": "localhost",
    "user": "logan",
    "database": "db"
}
connection = mysql.connector.connect(**db_config)
cursor = connection.cursor()

prof_table = """
CREATE TABLE Professor (
    professor_id INT AUTO_INCREMENT PRIMARY KEY,
    pr_name VARCHAR(255) UNIQUE
);
"""
class_table = """
CREATE TABLE Class (
    class_id VARCHAR(8) PRIMARY KEY,
    class_code varchar(8) NOT NULL 
);
"""
classsection_table = """
CREATE TABLE ClassSection (
    section_id INT AUTO_INCREMENT PRIMARY KEY,
    section_number INT, 
    class_id VARCHAR(8), 
    professor_id INT, 
    semester VARCHAR(10), 
    FOREIGN KEY (class_id) REFERENCES Class(class_id),
    FOREIGN KEY (professor_id) REFERENCES Professor(professor_id)
);
"""
gradeset_table = """
CREATE TABLE GradeSet (
    gradeset_id INT AUTO_INCREMENT PRIMARY KEY,
    section_id INT, 
    af INT, 
    gpa DECIMAL(4, 3),
    i INT,
    s INT,
    u INT,
    q INT,
    x INT,
    total INT,
    FOREIGN KEY (section_id) REFERENCES ClassSection(section_id)
);
"""
gradedist_table = """
CREATE TABLE GradeDistribution (
    gradedistribution_id INT AUTO_INCREMENT PRIMARY KEY,
    gradeset_id INT,
    grade ENUM('A', 'B', 'C', 'D', 'F', 'AF', 'I', 'S', 'U', 'Q', 'X') NOT NULL, 
    count INT, 
    percent DECIMAL(5, 2),
    FOREIGN KEY (gradeset_id) REFERENCES GradeSet(gradeset_id)
);
"""

table_arr = [prof_table, class_table, classsection_table, gradeset_table, gradedist_table]
for t in table_arr:
    try:
        cursor.execute(t)
        connection.commit()
        print("a table was created successfully...")
    except mysql.connector.Error as err:
        print(f"error: {err}")
        connection.rollback()

print("create tables complete...")

# --- extract grades ------------------------------------------------------------------------------------------------------------------------------------------------

print("extracting...")

pdf_file = open('grd20231EN.pdf', 'rb')
pdf_reader = PyPDF2.PdfReader(pdf_file)

classes = {}  # dict to store class info by class

# TODO: add more pdfs of other sems
semester = "Spring2023"

curr_class = None  # tracks the current class being processed
curr_section = None  # tracks the current section being processed
# curr_department = None # tracks the current department (line under "DEPARTMENT: ENGINEERING") for ez rmp search
dep_nxt = False
skip_header = False # extra tracking vars
grade_entry = False
total_entry = False
numstudents = 0 # ensure correct af/gpa
i = 0 # for gr/tot input proper indexing
section_number = 0
gpa = 0

for page_num in range(len(pdf_reader.pages)):
    page = pdf_reader.pages[page_num]
    lines = page.extract_text().split('\n')

    for line in lines:
        if skip_header:
            # next line contains department (for rmp query)
            if line.startswith("DEPARTMENT:"):
                dep_nxt = True
                continue
            if dep_nxt:
                parts = line.split()
                curr_department = ' '.join(parts)
                dep_nxt = False
                continue 

            # end of the header section
            if line.startswith("-------------------"):
                skip_header = False
            continue

        line = line.strip()

        # title / header, ignore if line is just...
        if line == "SECTION TEXAS A&M UNIVERSITY":
            continue

        # line before beginning of header
        if line.endswith("SECTION TEXAS A&M UNIVERSITY"):
            line = line[:-len("SECTION TEXAS A&M UNIVERSITY")].strip()

        # start of the header section
        if line.startswith("GRADE DISTRIBUTION REPORT FOR"):
            skip_header = True
            continue

        # temporary skipping of department totals...
        if line.startswith("DEPARTMENT TOTAL:"):
            skip_header = True
            continue

        # grade input
        if grade_entry == True:
            parts = line.split()
            if i != 4:
                percent = parts[0]
                percent = percent[:-1] # del % char
                classes[curr_class][0][0][section_number][i] = (classes[curr_class][0][0][section_number][i][0], float(percent))
                i += 1
                inum = parts[-1]
                numstudents += int(inum)
                classes[curr_class][0][0][section_number][i] = (int(inum), classes[curr_class][0][0][section_number][i][1])
            else:
                # last line of grades
                percent = parts[0]
                percent = percent[:-1] 
                classes[curr_class][0][0][section_number][i] = (classes[curr_class][0][0][section_number][i][0], float(percent))
                i += 1
                comb = parts[1] # af, gpa, i, s, u, q, x, total, prof
                af, j = 0, 0
                while af != numstudents:
                    af = int(comb[0:j+1])
                    j += 1

                try:
                    gpa = float(comb[j:]) 
                except:
                    gpa = gpa # take last gpa

                prof = ' '.join(parts[8:])
                classes[curr_class][0][0][section_number][5] = af
                classes[curr_class][0][0][section_number][6] = gpa
                classes[curr_class][0][0][section_number][7] = int(parts[2])
                classes[curr_class][0][0][section_number][8] = int(parts[3])
                classes[curr_class][0][0][section_number][9] = int(parts[4])
                classes[curr_class][0][0][section_number][10] = int(parts[5])
                classes[curr_class][0][0][section_number][11] = int(parts[6])
                classes[curr_class][0][0][section_number][12] = int(parts[7])
                classes[curr_class][0][0][section_number][13] = prof
                i = 0
                numstudents = 0
                grade_entry = False
                curr_section = None
            continue

        if total_entry == True:
            parts = line.split()
            if i != 4:
                percent = parts[0]
                percent = percent[:-1]
                classes[curr_class][0][1][i] = (classes[curr_class][0][1][i][0], float(percent)) 
                i += 1
                inum = parts[-1]
                numstudents += int(inum)
                classes[curr_class][0][1][i] = (int(inum), classes[curr_class][0][1][i][1]) 
            else:
                percent = parts[0]
                percent = percent[:-1] 
                classes[curr_class][0][1][i] = (classes[curr_class][0][1][i][0], float(percent))
                i += 1
                comb = parts[1]
                af, j = 0, 0
                while af != numstudents:
                    af = int(comb[0:j+1])
                    j += 1

                try:
                    gpa = float(comb[j:]) 
                except:
                    gpa = gpa # take last gpa

                classes[curr_class][0][1][5] = af
                classes[curr_class][0][1][6] = gpa
                classes[curr_class][0][1][7] = int(parts[2])
                classes[curr_class][0][1][8] = int(parts[3])
                classes[curr_class][0][1][9] = int(parts[4])
                classes[curr_class][0][1][10] = int(parts[5])
                classes[curr_class][0][1][11] = int(parts[6])
                classes[curr_class][0][1][12] = int(parts[7])
                i = 0
                numstudents = 0
                total_entry = False
                curr_class = None
            continue

        if line.startswith("COURSE TOTAL:"):
            # totals init
            if curr_class is not None:
                total_entry = True
                parts = line.split() # insert # As, start tot input
                totanum = parts[-1] 
                classes[curr_class][0][1][0] = (int(totanum), classes[curr_class][0][1][0][1])
                numstudents = int(totanum)
                i = 0
                
        else:
            # class init
            class_match = re.match(r'^([A-Z]+-\d+)(-\d+)?\s+', line)
            if class_match:
                # extract the class code and section number (if present)
                class_code = class_match.group(1)
                section_number = class_match.group(2)

                # removes the leading hyphen from the section number, make sure its an int
                if section_number:
                    section_number = section_number[1:]
                section_number = int(section_number)

                # create a new class entry if it doesn't exist
                if class_code not in classes:
                    classes[class_code] = []

                    curr_class = class_code # update the current class and section
                    curr_section = section_number

                    # create a new entry for the section in the classes dictionary
                    # a, b, c, d, f, af, gpa, i, s, u, q, x, total, prof
                    grarr = [(0, 0.0), (0, 0.0), (0, 0.0), (0, 0.0), (0, 0.0), (0), (0.0), (0), (0), (0), (0), (0), (0), ""]
                    toarr = [(0, 0.0), (0, 0.0), (0, 0.0), (0, 0.0), (0, 0.0), (0), (0.0), (0), (0), (0), (0), (0), (0)]
                    section_data = ({section_number : grarr}, toarr) 
                    classes[curr_class].append(section_data)

                else:
                    curr_section = section_number # new section of same class
                    grarr = [(0, 0.0), (0, 0.0), (0, 0.0), (0, 0.0), (0, 0.0), (0), (0.0), (0), (0), (0), (0), (0), (0), ""]
                    classes[curr_class][0][0][section_number] = grarr 

                parts = line.split() # insert # As, start gr input
                anum = parts[-1]
                classes[curr_class][0][0][section_number][0] = (int(anum), classes[curr_class][0][0][section_number][0][1])
                numstudents = int(anum)
                grade_entry = True
                i = 0

print("extract complete...")

# --- insert grades into db ------------------------------------------------------------------------------------------------------------------------------------------

# classes dictionary print AND INSERT INTO SQL DB
print("db populating...")

for class_code, sections in classes.items():
    # CSCE313, ({500 : [...], 501: [...],...}, tots)

    # insert class if not already in class table, then get new id
    insert = "INSERT IGNORE INTO Class (class_id) VALUES (%s)"
    cursor.execute(insert, (class_code,))
    connection.commit()
    cursor.fetchall() # fully consume before next exec
    cl_id_query = "SELECT class_id FROM Class WHERE class_id = %s"
    cursor.execute(cl_id_query, (class_code,))
    cl_id = cursor.fetchone()[0]
    cursor.fetchall()

    # insert section grades / info
    grs, tot = sections[0][0], sections[0][1] # grades, totals for class
    for section_num, grsarr in grs.items():
        # 500, [...]; 501, [...]

        # insert prof, then grab new id
        insert = """
        INSERT IGNORE INTO Professor (pr_name)
        VALUES (%s)
        """
        cursor.execute(insert, (grsarr[13],))
        connection.commit()
        cursor.fetchall() 
        pr_id_query = "SELECT professor_id FROM Professor WHERE pr_name = %s"
        cursor.execute(pr_id_query, (grsarr[13],))
        pr_id = cursor.fetchone()[0]
        cursor.fetchall() 

        # insert section # if not already in classsection table, then get new id
        insert = """
        INSERT IGNORE INTO ClassSection (section_number, class_id, professor_id, semester) 
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(insert, (section_num, cl_id, pr_id, semester)) # grsarr[13] == professor_name
        connection.commit()
        cursor.fetchall() 
        sect_id_query = "SELECT section_id FROM ClassSection WHERE section_number = %s AND class_id = %s"
        cursor.execute(sect_id_query, (section_num, cl_id,))
        sect_id = cursor.fetchone()[0]
        cursor.fetchall() 

        # insert gradeset for this section, then get new id
        # af, gpa, i, s, u, q, x, total
        insert = """
        INSERT INTO GradeSet (section_id, af, gpa, i, s, u, q, x, total)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert, (sect_id, grsarr[5], grsarr[6], grsarr[7], grsarr[8], grsarr[9], grsarr[10], grsarr[11], grsarr[12],))
        connection.commit()
        cursor.fetchall() 
        grset_id_query = "SELECT gradeset_id FROM GradeSet WHERE section_id = %s"
        cursor.execute(grset_id_query, (sect_id,))
        grset_id = cursor.fetchone()[0]
        cursor.fetchall()

        # insert gradedistribution for this gradeset & section, ref to gradeset
        for g in range(5):
            insert = """
            INSERT INTO GradeDistribution (gradeset_id, grade, count, percent)
            VALUES (%s, %s, %s, %s)
            """
            if g <= 3:
                cursor.execute(insert, (grset_id, chr(ord('A') + g), grsarr[g][0], grsarr[g][1],))
            else:
                cursor.execute(insert, (grset_id, chr(ord('A') + g + 1), grsarr[g][0], grsarr[g][1],))
            connection.commit()
            cursor.fetchall() 
        
print()
print("db complete...")

# --- del tables & close connection -----------------------------------------------------------------------------------------------------------------------------------------------

# drop to del, trunacte to clear
print("shutting down connection...")
# cursor.execute("DROP TABLE Professor")
# cursor.execute("DROP TABLE Class")
# cursor.execute("DROP TABLE ClassSection")
# cursor.execute("DROP TABLE GradeSet")
# cursor.execute("DROP TABLE GradeDistribution")
# connection.commit()
cursor.close()
connection.close()
print("connection shutdown.")

