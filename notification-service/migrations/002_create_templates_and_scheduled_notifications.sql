-- migration 002: create templates and scheduled_notifications

CREATE TABLE notification_templates (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL, -- identifier for template
  notification_type TEXT NOT NULL, -- e.g. booking_confirm, reminder, promo
  channel TEXT NOT NULL, -- email or sms
  subject_template TEXT, -- for email
  html_body_template TEXT, -- HTML email body
  sms_body_template TEXT, -- SMS text body
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE scheduled_notifications (
  id BIGSERIAL PRIMARY KEY,
  template_id BIGINT NOT NULL REFERENCES notification_templates(id) ON DELETE CASCADE,
  recipients JSONB NOT NULL, -- array of recipient addresses or phone numbers
  dynamic_data JSONB, -- JSON object for placeholder replacement
  schedule_at TIMESTAMPTZ NOT NULL,
  is_sent BOOLEAN DEFAULT false,
  sent_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now()
);