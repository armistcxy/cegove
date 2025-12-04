package sms

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
	"time"
)

var _ SMSProvider = (*VonageSender)(nil)

type VonageSender struct {
	apiKey    string
	apiSecret string
	from      string
	client    *http.Client
}

func NewVonageSender(apiKey, apiSecret, from string) *VonageSender {
	return &VonageSender{
		apiKey:    apiKey,
		apiSecret: apiSecret,
		from:      from,
		client: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

func (v *VonageSender) SendSMS(to string, body string) error {
	apiURL := "https://rest.nexmo.com/sms/json"
	cleanTo := strings.ReplaceAll(to, "+", "")
	data := url.Values{}
	data.Set("api_key", v.apiKey)
	data.Set("api_secret", v.apiSecret)
	data.Set("from", v.from)
	data.Set("text", body)
	data.Set("to", cleanTo)

	resp, err := v.client.PostForm(apiURL, data)
	if err != nil {
		return fmt.Errorf("lỗi kết nối mạng tới Vonage: %v", err)
	}
	defer resp.Body.Close()

	bodyBytes, err := io.ReadAll(resp.Body)
	if err != nil {
		return fmt.Errorf("không đọc được phản hồi: %v", err)
	}

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("vonage trả về http status %d: %s", resp.StatusCode, string(bodyBytes))
	}

	var vResp VonageResponse
	if err := json.Unmarshal(bodyBytes, &vResp); err != nil {
		return fmt.Errorf("lỗi parse json vonage: %v", err)
	}

	if len(vResp.Messages) > 0 {
		msg := vResp.Messages[0]
		if msg.Status != "0" {
			return fmt.Errorf("gửi thất bại (status=%s): %s", msg.Status, msg.ErrorText)
		}
	} else {
		return fmt.Errorf("phản hồi lạ từ vonage: không có message data")
	}

	return nil
}

type VonageResponse struct {
	MessageCount string `json:"message-count"`
	Messages     []struct {
		To               string `json:"to"`
		MessageID        string `json:"message-id"`
		Status           string `json:"status"`
		RemainingBalance string `json:"remaining-balance"`
		MessagePrice     string `json:"message-price"`
		Network          string `json:"network"`
		ErrorText        string `json:"error-text"`
	} `json:"messages"`
}
