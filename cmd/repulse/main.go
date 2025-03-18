package main

import (
	"database/sql"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"repulse/internal/storage"
	"repulse/internal/traffic"

	"github.com/joho/godotenv"
	_ "modernc.org/sqlite"
)

func loadEnv() {
	err := godotenv.Load()
	if err != nil {
		fmt.Println("Warning: No .env file found. Using system environment variables.")
	}
}

func generateGraphs() {
	fmt.Println("Generating graphs...")

	baseDirectory, err := os.Getwd()
	if err != nil {
		fmt.Println("Error getting base directory:", err)
		return
	}

	scriptPath := fmt.Sprintf("%s/analytics/generate_graphs.py", baseDirectory)
	cmd := exec.Command("python3", scriptPath)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	err = cmd.Run()
	if err != nil {
		fmt.Println("Error generating graphs:", err)
		return
	}

	fmt.Println("Graphs generated successfully.")
}

func getDatabasePath() (string, error) {
	baseDirectory, err := os.Getwd()
	if err != nil {
		return "", fmt.Errorf("error getting base directory: %v", err)
	}

	dbPath := filepath.Join(baseDirectory, "data", "github_traffic.db")

	err = os.MkdirAll(filepath.Dir(dbPath), os.ModePerm)
	if err != nil {
		return "", fmt.Errorf("error ensuring data directory exists: %v", err)
	}

	return dbPath, nil
}

func getEnvVars() (token string, owner string, repo string, err error) {
	loadEnv()

	envVarKeys := []string{"GH_TOKEN", "OWNER", "REPO"}
	var envVars []string

	for _, envVarKey := range envVarKeys {
		envVar := os.Getenv(envVarKey)
		if envVar == "" {
			return "", "", "", fmt.Errorf(
				"Error: %s is not set. Set %s in .env or as an environment variable.",
				envVarKey,
				envVarKey,
			)
		}

		envVars = append(envVars, envVar)
	}

	return envVars[0], envVars[1], envVars[2], nil
}

func main() {
	token, owner, repo, err := getEnvVars()
	if err != nil {
		fmt.Println(err)
		return
	}

	dbPath, err := getDatabasePath()
	if err != nil {
		fmt.Println(err)
		return
	}

	db, err := sql.Open("sqlite", dbPath)
	if err != nil {
		fmt.Println("Error opening database:", err)
		return
	}
	defer db.Close()

	trafficData := []traffic.TrafficResponse{
		&traffic.CloneData{},
		&traffic.ViewData{},
		&traffic.DownloadData{},
		&traffic.StarsData{},
	}

	for _, data := range trafficData {
		err = traffic.FetchTrafficData(token, owner, repo, &data)
		if err != nil {
			fmt.Printf("Error fetching %s data: %v\n", data.GetType(), err)
			return
		}

		fmt.Printf("API response (%s): %v\n\n", data.GetType(), data.GetData())

		err = storage.StoreTrafficData(db, data)
		if err != nil {
			fmt.Printf("Error storing %s data %v\n", data.GetType(), err)
			return
		}
	}

	generateGraphs()
}
