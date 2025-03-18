package storage

import (
	"database/sql"
	"fmt"
	"repulse/internal/traffic"
)

func StoreTrafficData[T traffic.TrafficResponse](db *sql.DB, data T) error {
	err := ensureTableExists(db)
	if err != nil {
		return err
	}

	if data.IsHistorical() {
		err = insertHistoricalData(db, data)
	} else {
		err = insertSnapshotData(db, data)
	}

	if err != nil {
		return err
	}

	fmt.Printf("%s data saved to SQLite database!\n", data.GetType())
	return nil
}

func insertHistoricalData[T traffic.TrafficResponse](db *sql.DB, data T) error {
	insertSql, err := buildHistoricalQuery(data.GetType())
	if err != nil {
		return err
	}

	statement, err := db.Prepare(insertSql)
	if err != nil {
		return fmt.Errorf("Error preparing SQL insert statement: %v", err)
	}
	defer statement.Close()

	for _, record := range data.GetData() {
		_, err = statement.Exec(record.Timestamp, record.Count, record.Uniques)
		if err != nil {
			return fmt.Errorf("Error inserting historical data into database: %v", err)
		}
	}

	return nil
}

func insertSnapshotData[T traffic.TrafficResponse](db *sql.DB, data T) error {
	insertSql, err := buildSnapshotQuery(data.GetType())
	if err != nil {
		return err
	}

	statement, err := db.Prepare(insertSql)
	if err != nil {
		return fmt.Errorf("Error preparing SQL insert statement: %v", err)
	}
	defer statement.Close()

	for _, record := range data.GetData() {
		_, err = statement.Exec(record.Timestamp, record.Count)
		if err != nil {
			return fmt.Errorf("Error inserting snapshot data into database: %v", err)
		}
	}

	return nil
}

func buildHistoricalQuery(dataType string) (string, error) {
	var column1 string
	var column2 string

	switch dataType {
	case traffic.TrafficClones, traffic.TrafficViews:
		column1 = dataType
		column2 = "unique_" + dataType
	default:
		return "", fmt.Errorf("Error: Unsupported historical type: %s", dataType)
	}

	return fmt.Sprintf(`
    INSERT INTO traffic (timestamp, %s, %s)
      VALUES (?, ?, ?)
      ON CONFLICT(timestamp) DO UPDATE
      SET %s = excluded.%s,
          %s = excluded.%s;
    `,
		column1, column2, column1, column1, column2, column2,
	), nil
}

func buildSnapshotQuery(dataType string) (string, error) {
	var column string

	switch dataType {
	case traffic.TrafficDownloads, traffic.TrafficStars:
		column = "total_" + dataType
	default:
		return "", fmt.Errorf("Error: Unsupported snapshot type: %s", dataType)
	}

	insertSql := fmt.Sprintf(`
			INSERT INTO traffic (timestamp, %s)
			VALUES (?, ?)
			ON CONFLICT(timestamp) DO UPDATE SET
				%s = excluded.%s;
		`, column, column, column)

	return insertSql, nil
}

func ensureTableExists(db *sql.DB) error {
	createTableSQL := `
    CREATE TABLE IF NOT EXISTS traffic (
		  id INTEGER PRIMARY KEY AUTOINCREMENT,
		  timestamp TEXT UNIQUE,
		  clones INTEGER DEFAULT 0,
		  unique_clones INTEGER DEFAULT 0,
		  views INTEGER DEFAULT 0,
		  unique_views INTEGER DEFAULT 0,
      total_downloads INTEGER DEFAULT 0,
		  total_stars INTEGER DEFAULT 0
	);
  `

	_, err := db.Exec(createTableSQL)
	if err != nil {
		return fmt.Errorf("Error creating table: %v", err)
	}

	return nil
}
