package notify

import (
	"context"
	"fmt"

	notification "github.com/armistcxy/cegove/notification-service/api"
	"github.com/armistcxy/cegove/notification-service/pkg/email"
	"github.com/armistcxy/cegove/notification-service/pkg/logging"
	"github.com/armistcxy/cegove/notification-service/pkg/sms"
)

// NotificationServiceImpl implements the NotificationService
type NotificationServiceImpl struct {
	notification.UnimplementedNotificationServiceServer
	emailProvider email.EmailProvider
	smsProvider   sms.SMSProvider
	logger        *logging.Logger
}

// NewNotificationServiceImpl creates a new instance of NotificationServiceImpl
func NewNotificationServiceImpl(emailProvider email.EmailProvider, smsProvider sms.SMSProvider, logger *logging.Logger) *NotificationServiceImpl {
	return &NotificationServiceImpl{
		emailProvider: emailProvider,
		smsProvider:   smsProvider,
		logger:        logger,
	}
}

// SendNotification sends a single notification email
func (s *NotificationServiceImpl) SendNotification(ctx context.Context, req *notification.SendNotificationRequest) (*notification.SendNotificationResponse, error) {
	if req == nil || len(req.To) == 0 {
		return &notification.SendNotificationResponse{
			Success: false,
			Message: "invalid request: recipients list is empty",
		}, nil
	}

	// Create email message from the request
	msg := &email.EmailMessage{
		To:       req.To,
		Subject:  req.Subject,
		HTMLBody: req.Body,
	}

	// Send the email
	result, err := s.emailProvider.SendEmail(ctx, msg)
	if err != nil {
		s.logger.Error("failed to send notification email", err)
		return &notification.SendNotificationResponse{
			Success: false,
			Message: fmt.Sprintf("failed to send email: %v", err),
		}, nil
	}

	s.logger.Info(fmt.Sprintf("notification sent successfully, message ID: %s", result.MessageID))
	return &notification.SendNotificationResponse{
		Success: true,
		Message: fmt.Sprintf("notification sent successfully, message ID: %s", result.MessageID),
	}, nil
}

// SendBatchNotification sends multiple notification emails in batch
func (s *NotificationServiceImpl) SendBatchNotification(ctx context.Context, req *notification.SendBatchNotificationRequest) (*notification.SendBatchNotificationResponse, error) {
	if req == nil || len(req.Notifications) == 0 {
		return &notification.SendBatchNotificationResponse{
			Results: []*notification.SendNotificationResponse{},
		}, nil
	}

	// Convert API notifications to email messages
	messages := make([]email.EmailMessage, len(req.Notifications))
	for i, notif := range req.Notifications {
		if len(notif.To) == 0 {
			messages[i] = email.EmailMessage{}
			continue
		}
		messages[i] = email.EmailMessage{
			To:       notif.To,
			Subject:  notif.Subject,
			HTMLBody: notif.Body,
		}
	}

	// Send emails in bulk
	results, err := s.emailProvider.SendBulkEmail(ctx, messages)
	if err != nil {
		s.logger.Error("failed to send batch notifications", err)
		// Still return partial results if some succeeded
	}

	// Convert results back to API format
	responses := make([]*notification.SendNotificationResponse, len(results))
	for i, result := range results {
		responses[i] = &notification.SendNotificationResponse{
			Success: true,
			Message: fmt.Sprintf("notification sent, message ID: %s", result.MessageID),
		}
	}

	s.logger.Info(fmt.Sprintf("batch notifications processed, sent %d emails", len(responses)))
	return &notification.SendBatchNotificationResponse{
		Results: responses,
	}, nil
}

// SendSMS sends a single SMS message
func (s *NotificationServiceImpl) SendSMS(ctx context.Context, req *notification.SendSMSRequest) (*notification.SendSMSResponse, error) {
	if len(req.To) == 0 {
		return &notification.SendSMSResponse{
			Success: false,
			Message: "Danh sách người nhận (to) không được để trống",
		}, nil
	}
	if req.Body == "" {
		return &notification.SendSMSResponse{
			Success: false,
			Message: "Nội dung tin nhắn trống",
		}, nil
	}

	err := s.smsProvider.SendSMS(req.To, req.Body)
	if err != nil {
		return nil, err
	}

	return &notification.SendSMSResponse{
		Success: true,
		Message: "SMS sent successfully.",
	}, nil
}
