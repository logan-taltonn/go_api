SELECT
    c.class_id,
    cs.semester,
    cs.section_number,
    gd_summary.a_cnt,
    gd_summary.a_perc,
    gd_summary.b_cnt,
    gd_summary.b_perc,
    gd_summary.c_cnt,
    gd_summary.c_perc,
    gd_summary.d_cnt,
    gd_summary.d_perc,
    gd_summary.f_cnt,
    gd_summary.f_perc,
    gds.af,
    AVG(gds.gpa) AS avg_gpa,
    gds.i,
    gds.s,
    gds.u,
    gds.q,
    gds.x,
    gds.total
FROM Professor prof
JOIN ClassSection cs ON prof.professor_id = cs.professor_id
JOIN GradeSet gds ON cs.section_id = gds.section_id
JOIN Class c ON cs.class_id = c.class_id
LEFT JOIN (
    SELECT
        gds.section_id,
        SUM(CASE WHEN gd.grade = 'A' THEN gd.count ELSE 0 END) AS a_cnt,
        MAX(gd_a.percent) AS a_perc,
        SUM(CASE WHEN gd.grade = 'B' THEN gd.count ELSE 0 END) AS b_cnt,
        MAX(gd_b.percent) AS b_perc,
        SUM(CASE WHEN gd.grade = 'C' THEN gd.count ELSE 0 END) AS c_cnt,
        MAX(gd_c.percent) AS c_perc,
        SUM(CASE WHEN gd.grade = 'D' THEN gd.count ELSE 0 END) AS d_cnt,
        MAX(gd_d.percent) AS d_perc,
        SUM(CASE WHEN gd.grade = 'F' THEN gd.count ELSE 0 END) AS f_cnt,
        MAX(gd_f.percent) AS f_perc
    FROM GradeSet gds
    JOIN GradeDistribution gd ON gds.gradeset_id = gd.gradeset_id
    LEFT JOIN GradeDistribution gd_a ON gds.gradeset_id = gd_a.gradeset_id AND gd_a.grade = 'A'
    LEFT JOIN GradeDistribution gd_b ON gds.gradeset_id = gd_b.gradeset_id AND gd_b.grade = 'B'
    LEFT JOIN GradeDistribution gd_c ON gds.gradeset_id = gd_c.gradeset_id AND gd_c.grade = 'C'
    LEFT JOIN GradeDistribution gd_d ON gds.gradeset_id = gd_d.gradeset_id AND gd_d.grade = 'D'
    LEFT JOIN GradeDistribution gd_f ON gds.gradeset_id = gd_f.gradeset_id AND gd_f.grade = 'F'
    GROUP BY gds.section_id
) gd_summary ON cs.section_id = gd_summary.section_id
WHERE prof.pr_name = ?
GROUP BY
    c.class_id,
    cs.semester,
    cs.section_number,
    gd_summary.a_cnt,
    gd_summary.a_perc,
    gd_summary.b_cnt,
    gd_summary.b_perc,
    gd_summary.c_cnt,
    gd_summary.c_perc,
    gd_summary.d_cnt,
    gd_summary.d_perc,
    gd_summary.f_cnt,
    gd_summary.f_perc,
    gds.af,
    gds.i,
    gds.s,
    gds.u,
    gds.q,
    gds.x,
    gds.total;