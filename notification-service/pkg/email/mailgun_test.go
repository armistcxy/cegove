package email

import (
	"context"
	"os"
	"testing"
)

func TestMailgunSendEmail(t *testing.T) {
	mailgunAPIKey := os.Getenv("MAILGUN_API_KEY")
	if mailgunAPIKey == "" {
		t.Skip("MAILGUN_API_KEY is not set")
	}

	mailgunSandboxDomain := os.Getenv("MAILGUN_DOMAIN")
	if mailgunSandboxDomain == "" {
		t.Skip("MAILGUN_DOMAIN is not set")
	}

	receiverEmail := os.Getenv("RECEIVER_EMAIL")

	// Create a new MailgunProvider
	provider, err := NewMailgunProvider(mailgunSandboxDomain, mailgunAPIKey, "")
	if err != nil {
		t.Fatalf("failed to create mailgun provider: %v", err)
	}

	msg := &EmailMessage{
		To:      []string{receiverEmail},
		Subject: "Test Email",
		TextBody: "This is a test email sent from MailgunProvider. " +
			"If you receive this email, it means the MailgunProvider is working correctly.",
	}

	result, err := provider.SendEmail(context.Background(), msg)
	if err != nil {
		t.Fatalf("failed to send email: %v", err)
	}

	if result == nil {
		t.Fatal("result is nil")
	}

	t.Logf("Message sent successfully with ID: %s", result.MessageID)
}
