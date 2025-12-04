package email

// EmailMessage defines informations of email messages
type EmailMessage struct {
	From        string
	FromName    string
	To          []string
	CC          []string
	BCC         []string
	Subject     string
	TextBody    string
	HTMLBody    string
	Attachments []Attachment
	ReplyTo     string
	Headers     map[string]string
}

// Attachment defines informations of email attachments
type Attachment struct {
	Filename    string
	Content     []byte
	ContentType string
}

// SendResult contains informations of email send result
type SendResult struct {
	MessageID string
}
