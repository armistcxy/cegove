package email

import (
	"context"
	"fmt"
	"time"

	"github.com/mailgun/mailgun-go/v4"
)

var _ EmailProvider = (*MailgunProvider)(nil)

// MailgunProvider implements the EmailProvider interface using Mailgun
type MailgunProvider struct {
	mg          mailgun.Mailgun
	defaultFrom string
}

// NewMailgunProvider creates a new MailgunProvider
func NewMailgunProvider(domain, apiKey, defaultFrom string) (*MailgunProvider, error) {
	if domain == "" {
		return nil, fmt.Errorf("domain is required")
	}
	if apiKey == "" {
		return nil, fmt.Errorf("apiKey is required")
	}

	// if defaultFrom is not provided, use postmaster@domain as defaultFrom
	if defaultFrom == "" {
		defaultFrom = "postmaster@" + domain
	}

	mg := mailgun.NewMailgun(domain, apiKey)
	return &MailgunProvider{
		mg:          mg,
		defaultFrom: defaultFrom,
	}, nil
}

// buildMailgunMessage is a helper function to construct a mailgun.Message from our EmailMessage
func (p *MailgunProvider) buildMailgunMessage(msg *EmailMessage) *mailgun.Message {
	// Format the "From" field with an optional name
	from := msg.From
	if msg.FromName != "" {
		from = fmt.Sprintf("%s <%s>", msg.FromName, msg.From)
	}

	// fallback to defaultFrom if from is empty
	if from == "" {
		from = p.defaultFrom
	}

	// Create the message with basic info
	message := mailgun.NewMessage(from, msg.Subject, msg.TextBody, msg.To...)

	// Set HTML body if provided
	if msg.HTMLBody != "" {
		message.SetHTML(msg.HTMLBody)
	}

	// Add CC and BCC recipients
	for _, cc := range msg.CC {
		message.AddCC(cc)
	}
	for _, bcc := range msg.BCC {
		message.AddBCC(bcc)
	}

	// Add attachments
	for _, att := range msg.Attachments {
		message.AddBufferAttachment(att.Filename, att.Content)
	}

	// Set Reply-To address if provided
	if msg.ReplyTo != "" {
		message.SetReplyTo(msg.ReplyTo)
	}

	// Add custom headers
	for key, value := range msg.Headers {
		message.AddHeader(key, value)
	}

	return message
}

// SendEmail sends a single email message
func (p *MailgunProvider) SendEmail(ctx context.Context, msg *EmailMessage) (*SendResult, error) {
	mailgunMsg := p.buildMailgunMessage(msg)

	_, id, err := p.mg.Send(ctx, mailgunMsg)
	if err != nil {
		return nil, err
	}

	return &SendResult{
		MessageID: id,
	}, nil
}

// SendTemplateEmail sends an email using a Mailgun template
func (p *MailgunProvider) SendTemplateEmail(ctx context.Context, templateID string, to []string, data map[string]interface{}) (*SendResult, error) {
	mailgunMsg := p.buildMailgunMessage(&EmailMessage{
		To:   to,
		From: p.defaultFrom,
	})
	mailgunMsg.SetTemplate(templateID)

	for key, value := range data {
		if err := mailgunMsg.AddTemplateVariable(key, value); err != nil {
			return nil, fmt.Errorf("failed to add template variable %s: %w", key, err)
		}
	}

	ctx, cancel := context.WithTimeout(ctx, time.Second*10)
	defer cancel()

	_, id, err := p.mg.Send(ctx, mailgunMsg)
	if err != nil {
		return nil, err
	}

	return &SendResult{
		MessageID: id,
	}, nil
}

// SendBulkEmail sends multiple email messages.
func (p *MailgunProvider) SendBulkEmail(ctx context.Context, messages []EmailMessage) ([]SendResult, error) {
	if len(messages) == 0 {
		return []SendResult{}, nil
	}

	results := make([]SendResult, 0, len(messages))

	for _, msg := range messages {
		mailgunMsg := p.buildMailgunMessage(&msg)

		_, id, err := p.mg.Send(ctx, mailgunMsg)
		if err != nil {
			results = append(results, SendResult{
				MessageID: fmt.Sprintf("error: %v", err),
			})
			continue
		}

		results = append(results, SendResult{
			MessageID: id,
		})
	}

	return results, nil
}

// GetProviderName returns the name of the provider
func (p *MailgunProvider) GetProviderName() string {
	return "Mailgun"
}
