package sms

import (
	"fmt"

	"github.com/twilio/twilio-go"
	api "github.com/twilio/twilio-go/rest/api/v2010"
)

var _ SMSProvider = (*TwilioSender)(nil)

type TwilioSender struct {
	client    *twilio.RestClient
	fromPhone string
}

func NewTwilioSender(apiKey, apiSecret, fromPhone string) *TwilioSender {
	client := twilio.NewRestClientWithParams(twilio.ClientParams{
		Username: apiKey,
		Password: apiSecret,
	})
	return &TwilioSender{
		client:    client,
		fromPhone: fromPhone,
	}
}

func (t *TwilioSender) SendSMS(to string, body string) error {
	params := &api.CreateMessageParams{}
	params.SetTo(to)
	params.SetFrom(t.fromPhone)
	params.SetBody(body)

	_, err := t.client.Api.CreateMessage(params)
	if err != nil {
		return fmt.Errorf("twilio error: %v", err)
	}
	return nil
}
