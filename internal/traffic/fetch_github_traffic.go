package traffic

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

const (
	APIAcceptType  = "application/vnd.github.v3+json"
	RequestTimeout = 10 * time.Second
)

func FetchTrafficData[T TrafficResponse](
	token string,
	owner string,
	repo string,
	result *T,
) error {
	dataType := (*result).GetType()
	fmt.Printf("Fetching %s data from GitHub API...\n", dataType)
	fmt.Println((*result).BuildUrl(owner, repo))

	baseUrl := (*result).BuildUrl(owner, repo)
	if dataType == TrafficDownloads {
		return fetchPaginatedReleases(token, baseUrl, result)
	}

	response, err := makeGitHubRequest(token, baseUrl)
	if err != nil {
		return fmt.Errorf("Error making %s request: %v\n", dataType, err)
	}
	defer response.Body.Close()

	bodyBytes, err := readResponseBody(response.Body, dataType)
	if err != nil {
		return err
	}

	err = parseJson(bodyBytes, result)
	if err != nil {
		return err
	}

	fmt.Printf("%s data successfully fetched!\n", dataType)

	return nil
}

func fetchPaginatedReleases[T TrafficResponse](token string, baseUrl string, result *T) error {
	var allReleases []Release
	page := 1

	for {
		url := fmt.Sprintf("%s&page=%d", baseUrl, page)
		response, err := makeGitHubRequest(token, url)
		if err != nil {
			return fmt.Errorf("Error fetching releases (page %d): %v", page, err)
		}
		defer response.Body.Close()

		var pageReleases []Release
		bodyBytes, err := readResponseBody(response.Body, "downloads")
		if err != nil {
			return err
		}

		err = json.Unmarshal(bodyBytes, &pageReleases)
		if err != nil {
			return fmt.Errorf("Error parsing release page JSON (page %d): %v", page, err)
		}

		fmt.Println(len(pageReleases))

		if len(pageReleases) == 0 {
			break
		}

		allReleases = append(allReleases, pageReleases...)
		page++
	}

	downloadData, ok := any(*result).(*DownloadData)
	if !ok {
		return fmt.Errorf("unexpected type for downloads: %T", *result)
	}

	downloadData.Releases = allReleases

	fmt.Printf("Successfully fetched %d release(s).\n", len(allReleases))
	return nil
}

func parseJson[T TrafficResponse](bodyBytes []byte, result *T) error {
	err := (*result).ParseJson(bodyBytes, result)
	if err != nil {
		return fmt.Errorf("Error parsing %s JSON: %v", (*result).GetType(), err)
	}

	return nil
}

func readResponseBody(body io.Reader, dataType string) ([]byte, error) {
	bodyBytes, err := io.ReadAll(body)
	if err != nil {
		return nil, fmt.Errorf("Error reading %s response body: %v", dataType, err)
	}

	return bodyBytes, nil
}

func makeGitHubRequest(token string, url string) (*http.Response, error) {
	req, err := getRequest(token, url)
	if err != nil {
		return nil, err
	}

	client := &http.Client{Timeout: RequestTimeout}
	response, err := client.Do(req)
	if err != nil {
		return nil, err
	}

	return response, nil
}

func getRequest(token string, url string) (*http.Request, error) {
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("Error creating request object: %v", err)
	}

	req.Header.Set("Authorization", "token "+token)
	req.Header.Set("Accept", APIAcceptType)

	return req, nil
}
