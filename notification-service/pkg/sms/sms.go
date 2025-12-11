package sms

type SMSProvider interface {
	SendSMS(to string, body string) error
}
