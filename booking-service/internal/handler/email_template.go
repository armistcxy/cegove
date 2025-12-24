package handler

import (
	"fmt"
	"strings"
	"time"

	"github.com/armistcxy/cegove/booking-service/internal/domain"
)

// GenerateBookingConfirmationEmail generates an HTML email body for booking confirmation with QR codes
func GenerateBookingConfirmationEmail(booking *domain.Booking, userEmail string) string {
	const emailTemplate = `<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Booking Confirmation - CeGove Cinema</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
            background-color: #f5f5f5;
            color: #333;
        }

        .email-container {
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            text-align: center;
        }

        .header h1 {
            font-size: 28px;
            margin-bottom: 8px;
            font-weight: 700;
        }

        .header p {
            font-size: 14px;
            opacity: 0.9;
        }

        .content {
            padding: 40px 20px;
        }

        .confirmation-message {
            background-color: #f0f7ff;
            border-left: 4px solid #667eea;
            padding: 16px;
            margin-bottom: 30px;
            border-radius: 4px;
        }

        .confirmation-message h2 {
            color: #667eea;
            font-size: 18px;
            margin-bottom: 8px;
        }

        .confirmation-message p {
            color: #555;
            font-size: 14px;
            line-height: 1.6;
        }

        .section-title {
            font-size: 18px;
            font-weight: 700;
            color: #333;
            margin: 30px 0 20px 0;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }

        .booking-info {
            background-color: #f9f9f9;
            padding: 20px;
            border-radius: 6px;
            margin-bottom: 20px;
        }

        .info-row {
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid #e0e0e0;
            gap: 20px;
        }

        .info-row:last-child {
            border-bottom: none;
        }

        .info-label {
            font-weight: 600;
            color: #666;
            font-size: 13px;
            text-transform: uppercase;
            min-width: 120px;
        }

        .info-value {
            color: #333;
            font-size: 14px;
            text-align: right;
            flex: 1;
        }

        .tickets-container {
            margin-top: 30px;
        }

        .ticket-card {
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            background-color: #fafafa;
            page-break-inside: avoid;
        }

        .ticket-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 20px;
            border-bottom: 1px solid #e0e0e0;
            padding-bottom: 15px;
        }

        .movie-info h3 {
            font-size: 16px;
            font-weight: 700;
            color: #333;
            margin-bottom: 6px;
        }

        .cinema-info {
            font-size: 13px;
            color: #666;
            line-height: 1.5;
        }

        .qr-code-container {
            text-align: center;
            padding: 15px 0;
        }

        .qr-code-image {
            width: 150px;
            height: 150px;
            border: 2px solid #667eea;
            border-radius: 6px;
            padding: 8px;
            background-color: white;
        }

        .qr-label {
            font-size: 12px;
            color: #999;
            margin-top: 8px;
            font-weight: 600;
            text-transform: uppercase;
        }

        .ticket-details {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-top: 15px;
        }

        .ticket-detail {
            font-size: 13px;
        }

        .ticket-detail-label {
            color: #999;
            font-size: 11px;
            text-transform: uppercase;
            margin-bottom: 4px;
            font-weight: 600;
        }

        .ticket-detail-value {
            color: #333;
            font-size: 14px;
            font-weight: 600;
        }

        .ticket-seat {
            font-size: 14px;
            font-weight: 700;
            color: #667eea;
        }

        .price-section {
            background-color: #f0f7ff;
            padding: 20px;
            border-radius: 6px;
            margin-top: 30px;
        }

        .price-row {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            font-size: 14px;
        }

        .price-row.total {
            border-top: 2px solid #667eea;
            padding-top: 12px;
            margin-top: 12px;
            font-weight: 700;
            font-size: 16px;
            color: #667eea;
        }

        .action-section {
            margin-top: 30px;
            text-align: center;
        }

        .btn {
            display: inline-block;
            padding: 12px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 600;
            font-size: 14px;
            transition: opacity 0.2s;
        }

        .btn:hover {
            opacity: 0.9;
        }

        .important-notice {
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
            font-size: 13px;
            color: #856404;
            line-height: 1.6;
        }

        .important-notice strong {
            display: block;
            margin-bottom: 8px;
            color: #333;
        }

        .footer {
            background-color: #f5f5f5;
            padding: 20px;
            text-align: center;
            border-top: 1px solid #e0e0e0;
            font-size: 12px;
            color: #666;
        }

        .footer p {
            margin: 5px 0;
        }

        .contact-info {
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #e0e0e0;
        }

        @media (max-width: 600px) {
            .email-container {
                border-radius: 0;
            }

            .content {
                padding: 20px;
            }

            .ticket-details {
                grid-template-columns: 1fr;
            }

            .info-row {
                flex-direction: column;
            }

            .info-value {
                text-align: left;
                margin-top: 4px;
            }

            .qr-code-image {
                width: 120px;
                height: 120px;
            }
        }
    </style>
</head>
<body>
    <div class="email-container">
        <!-- Header -->
        <div class="header">
            <h1>🎬 Booking Confirmed!</h1>
            <p>Your cinema tickets are ready</p>
        </div>

        <!-- Content -->
        <div class="content">
            <!-- Confirmation Message -->
            <div class="confirmation-message">
                <h2>Thank you for your booking!</h2>
                <p>Your booking has been confirmed. Below you'll find all the details. Please present your QR code at the cinema entrance.</p>
            </div>

            <!-- Booking Details -->
            <div class="section-title">Booking Details</div>
            <div class="booking-info">
                <div class="info-row">
                    <span class="info-label">Booking ID</span>
                    <span class="info-value">{{BOOKING_ID}}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Booking Date</span>
                    <span class="info-value">{{BOOKING_DATE}}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Email</span>
                    <span class="info-value">{{USER_EMAIL}}</span>
                </div>
            </div>

            <!-- Booking QR Code -->
            <div style="text-align: center; margin: 30px 0; padding: 20px; background-color: #f9f9f9; border-radius: 6px;">
                <div style="font-size: 14px; font-weight: 600; color: #333; margin-bottom: 15px;">Your Booking QR Code</div>
                {{BOOKING_QR_CODE}}
            </div>

            <!-- Tickets -->
            <div class="section-title">Your Tickets</div>
            <div class="tickets-container">
                {{TICKETS}}
            </div>

            <!-- Price Summary -->
            <div class="price-section">
                <div class="price-row">
                    <span>Subtotal ({{TICKET_COUNT}} tickets)</span>
                    <span>{{SUBTOTAL}}</span>
                </div>
                <div class="price-row total">
                    <span>Total Amount</span>
                    <span>{{TOTAL_PRICE}}</span>
                </div>
            </div>

            <!-- Important Notice -->
            <div class="important-notice">
                <strong>⚠️ Important Information</strong>
                <ul style="margin: 8px 0; padding-left: 20px;">
                    <li>Please arrive 15 minutes before showtime</li>
                    <li>Present your QR code at the ticket counter for seat confirmation</li>
                    <li>Keep this email for reference</li>
                    <li>Cancellations must be made at least 2 hours before showtime</li>
                </ul>
            </div>

            <!-- Action Section -->
            <div class="action-section">
                <a href="{{BOOKING_URL}}" class="btn">View My Booking</a>
            </div>
        </div>

        <!-- Footer -->
        <div class="footer">
            <p><strong>CeGove Cinema</strong></p>
            <div class="contact-info">
                <p>📞 Customer Support: +84 (0) 123 456 789</p>
                <p>📧 Email: support@cegove.cinema</p>
                <p>🌐 Website: www.cegove.cinema</p>
            </div>
            <p style="margin-top: 15px; color: #999;">
                © {{CURRENT_YEAR}} CeGove Cinema. All rights reserved.
            </p>
        </div>
    </div>
</body>
</html>
`

	// Generate ticket HTML
	ticketsHTML := generateTicketsHTML(booking.Tickets)

	// Calculate totals
	subtotal := calculateSubtotal(booking.Tickets)
	totalPrice := booking.TotalPrice

	// Convert to UTC+7 timezone
	loc, err := time.LoadLocation("Asia/Bangkok")
	if err != nil {
		// Fallback to UTC if location cannot be loaded
		loc = time.UTC
	}
	bookingDateUTC7 := booking.CreatedAt.In(loc)

	// Generate booking QR code HTML
	bookingQRCodeHTML := ""
	if booking.ID != "" {
		bookingQRCodeHTML = fmt.Sprintf(`
                <div class="qr-code-container">
                    <img src="%s" alt="Booking QR Code" class="qr-code-image" />
                    <div class="qr-label">Scan for Entry</div>
                </div>
            `, booking.ID)
	} else {
		bookingQRCodeHTML = `
                <div class="qr-code-container">
                    <div style="width: 150px; height: 150px; border: 2px solid #ddd; border-radius: 6px; display: flex; align-items: center; justify-content: center; background-color: #f5f5f5; margin: 0 auto;">
                        <div style="text-align: center; color: #999;">
                            <p style="font-size: 12px; margin: 0;">QR Code</p>
                            <p style="font-size: 11px; margin: 5px 0 0 0;">Coming Soon</p>
                        </div>
                    </div>
                    <div class="qr-label">Scan for Entry</div>
                </div>
            `
	}

	// Replace placeholders
	html := emailTemplate
	html = strings.ReplaceAll(html, "{{BOOKING_ID}}", booking.ID)
	html = strings.ReplaceAll(html, "{{BOOKING_DATE}}", bookingDateUTC7.Format("January 02, 2006 at 15:04"))
	html = strings.ReplaceAll(html, "{{USER_EMAIL}}", userEmail)
	html = strings.ReplaceAll(html, "{{TICKETS}}", ticketsHTML)
	html = strings.ReplaceAll(html, "{{BOOKING_QR_CODE}}", bookingQRCodeHTML)
	html = strings.ReplaceAll(html, "{{TICKET_COUNT}}", fmt.Sprintf("%d", len(booking.Tickets)))
	html = strings.ReplaceAll(html, "{{SUBTOTAL}}", formatPrice(subtotal))
	html = strings.ReplaceAll(html, "{{TOTAL_PRICE}}", formatPrice(totalPrice))
	html = strings.ReplaceAll(html, "{{BOOKING_URL}}", fmt.Sprintf("https://cegove.cinema/bookings/%s", booking.ID))
	html = strings.ReplaceAll(html, "{{CURRENT_YEAR}}", fmt.Sprintf("%d", time.Now().Year()))

	return html
}

// generateTicketsHTML generates HTML for all tickets with QR codes
func generateTicketsHTML(tickets []domain.Ticket) string {
	var html strings.Builder
	loc, err := time.LoadLocation("Asia/Bangkok")
	if err != nil {
		// Fallback to UTC if location cannot be loaded
		loc = time.UTC
	}

	for i, ticket := range tickets {
		showtimeUTC7 := ticket.Showtime.In(loc)

		html.WriteString(fmt.Sprintf(`
    <div class="ticket-card">
        <div class="ticket-header">
            <div class="movie-info">
                <h3>%s</h3>
                <div class="cinema-info">
                    <p>📍 %s | %s</p>
                    <p>🕐 %s</p>
                </div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 12px; color: #999; text-transform: uppercase; margin-bottom: 8px; font-weight: 600;">Ticket %d</div>
            </div>
        </div>

        <div class="ticket-details">
            <div class="ticket-detail">
                <div class="ticket-detail-label">Seat</div>
                <div class="ticket-seat">%s</div>
            </div>
            <div class="ticket-detail">
                <div class="ticket-detail-label">Price</div>
                <div class="ticket-detail-value">%s</div>
            </div>
            <div class="ticket-detail">
                <div class="ticket-detail-label">Status</div>
                <div class="ticket-detail-value" style="color: #28a745;">Active</div>
            </div>
            <div class="ticket-detail">
                <div class="ticket-detail-label">Ticket ID</div>
                <div class="ticket-detail-value" style="font-size: 12px; word-break: break-all;">%s</div>
            </div>
        </div>
    </div>
`, ticket.MovieTitle, ticket.CinemaName, ticket.AuditoriumName,
			showtimeUTC7.Format("Monday, January 02, 2006 at 15:04"),
			i+1,
			ticket.SeatNumber,
			formatPrice(ticket.Price),
			ticket.ID))
	}

	return html.String()
}

// calculateSubtotal calculates the sum of all ticket prices
func calculateSubtotal(tickets []domain.Ticket) float64 {
	var total float64
	for _, ticket := range tickets {
		total += ticket.Price
	}
	return total
}

// formatPrice formats a price as a currency string
func formatPrice(price float64) string {
	return fmt.Sprintf("₫%.0f", price) // Vietnamese Dong - adjust as needed
}
