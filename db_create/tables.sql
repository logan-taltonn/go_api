CREATE TABLE Professor (
    professor_id INT AUTO_INCREMENT PRIMARY KEY,
    pr_name VARCHAR(255) UNIQUE
);

CREATE TABLE Class (
    class_id VARCHAR(8) PRIMARY KEY,
    class_code varchar(8) NOT NULL, 
);

CREATE TABLE ClassSection (
    section_id INT AUTO_INCREMENT PRIMARY KEY,
    section_number INT, 
    class_id VARCHAR(8), 
    professor_id INT, 
    semester VARCHAR(10), 
    FOREIGN KEY (class_id) REFERENCES Class(class_id),
    FOREIGN KEY (professor_id) REFERENCES Professor(professor_id)
);

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

CREATE TABLE GradeDistribution (
    gradedistribution_id INT AUTO_INCREMENT PRIMARY KEY,
    gradeset_id INT,
    grade ENUM('A', 'B', 'C', 'D', 'F', 'AF', 'I', 'S', 'U', 'Q', 'X') NOT NULL, 
    count INT, 
    percent DECIMAL(5, 2),
    FOREIGN KEY (gradeset_id) REFERENCES GradeSet(gradeset_id)
);