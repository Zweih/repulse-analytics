package traffic

import (
	"encoding/json"
	"fmt"
	"time"
)

const (
	GitHubBaseURL    = "https://api.github.com/repos"
	trafficPath      = "traffic"
	TrafficClones    = "clones"
	TrafficViews     = "views"
	TrafficDownloads = "downloads"
	TrafficStars     = "stars"
)

type BaseTrafficData struct{}

func (b *BaseTrafficData) ParseJson(data []byte, v any) error {
	return json.Unmarshal(data, v)
}

type TrafficDay struct {
	Timestamp string `json:"timestamp"`
	Count     int    `json:"count"`
	Uniques   int    `json:"uniques"`
}

type TrafficResponse interface {
	GetData() []TrafficDay
	GetType() string
	BuildUrl(owner string, repo string) string
	IsHistorical() bool
	ParseJson(data []byte, v any) error
}

func buildHistoricalUrl(owner string, repo string, dataType string) string {
	return fmt.Sprintf("%s/%s/%s", buildRepoUrl(owner, repo), trafficPath, dataType)
}

func buildRepoUrl(owner string, repo string) string {
	return fmt.Sprintf("%s/%s/%s", GitHubBaseURL, owner, repo)
}

type CloneData struct {
	BaseTrafficData
	Count   int          `json:"count"`
	Uniques int          `json:"uniques"`
	Clones  []TrafficDay `json:"clones"`
}

func (c CloneData) GetData() []TrafficDay {
	return c.Clones
}

func (c CloneData) GetType() string {
	return TrafficClones
}

func (c CloneData) IsHistorical() bool {
	return true
}

func (c CloneData) BuildUrl(owner string, repo string) string {
	return buildHistoricalUrl(owner, repo, c.GetType())
}

type ViewData struct {
	BaseTrafficData
	Count   int          `json:"count"`
	Uniques int          `json:"uniques"`
	Views   []TrafficDay `json:"views"`
}

func (v ViewData) GetData() []TrafficDay {
	return v.Views
}

func (v ViewData) GetType() string {
	return TrafficViews
}

func (v ViewData) IsHistorical() bool {
	return true
}

func (v ViewData) BuildUrl(owner string, repo string) string {
	return buildHistoricalUrl(owner, repo, v.GetType())
}

type ReleaseAsset struct {
	Name          string `json:"name"`
	DownloadCount int    `json:"download_count"`
}

type Release struct {
	TagName     string         `json:"tag_name"`
	PublishedAt string         `json:"published_at"`
	Assets      []ReleaseAsset `json:"assets"`
}

type DownloadData struct {
	Releases []Release
}

func (d DownloadData) GetData() []TrafficDay {
	totalDownloads := 0

	for _, release := range d.Releases {
		for _, asset := range release.Assets {
			totalDownloads += asset.DownloadCount
		}
	}

	return []TrafficDay{
		{
			Timestamp: roundToUtcMidnightToday(), // github API is in UTC time
			Count:     totalDownloads,
		},
	}
}

func (d *DownloadData) ParseJson(data []byte, _ any) error {
	return json.Unmarshal(data, &d.Releases)
}

func (d DownloadData) GetType() string {
	return TrafficDownloads
}

func (d DownloadData) IsHistorical() bool {
	return false
}

func (d DownloadData) BuildUrl(owner string, repo string) string {
	return fmt.Sprintf("%s/releases?per_page=100", buildRepoUrl(owner, repo))
}

type StarsData struct {
	BaseTrafficData
	TotalStars int `json:"stargazers_count"`
}

func (s StarsData) GetData() []TrafficDay {
	return []TrafficDay{
		{
			Timestamp: roundToUtcMidnightToday(),
			Count:     s.TotalStars,
		},
	}
}

func (s StarsData) GetType() string {
	return TrafficStars
}

func (s StarsData) IsHistorical() bool {
	return false
}

func (s StarsData) BuildUrl(owner string, repo string) string {
	return buildRepoUrl(owner, repo)
}

func roundToUtcMidnightToday() string {
	t := time.Now().UTC()
	midnight := time.Date(t.Year(), t.Month(), t.Day(), 0, 0, 0, 0, time.UTC)
	return midnight.Format(time.RFC3339)
}
