# How to Fix SendGrid "Sender Identity" Error

The job automation system failed to send the email because SendGrid requires you to **verify ownership** of the email address you are sending *from*.

You are currently trying to send as: `matusaltaner@gmail.com` or `noreply@curak.xyz`.
SendGrid blocked this because neither of these has been authorized in your SendGrid account.

## Option 1: The Quick Fix (Single Sender Verification)
*Best if you just want to get it working immediately using your Gmail.*

1.  **Log in to SendGrid**: [https://app.sendgrid.com](https://app.sendgrid.com)
2.  Navigate to **Settings** → **Sender Authentication**.
3.  Click **Verify a Single Sender**.
4.  **Create New Sender**:
    *   **From Name**: Matus Altaner (or whatever you want to appear)
    *   **From Email Address**: `matusaltaner@gmail.com` (Must match what is in your `.env` file)
    *   **Reply To**: `matusaltaner@gmail.com`
    *   Fill in the address fields (can be approximate).
5.  Click **Create**.
6.  **Check your Gmail inbox** for a verification email from SendGrid.
7.  **Click the link** in that email to verify.
8.  **Done!** You can now run the script again.

## Option 2: The Professional Fix (Domain Authentication)
*Best for `noreply@curak.xyz` - improves delivery rates and looks professional.*

1.  **Log in to SendGrid**: [https://app.sendgrid.com](https://app.sendgrid.com)
2.  Navigate to **Settings** → **Sender Authentication**.
3.  Click **Authenticate Your Domain**.
4.  **Choose DNS Host**: Select "Cloudflare" (since you mentioned using it) or "Other".
5.  **Brand Your Links**: Select "No" (simpler setup).
6.  **Enter Domain**: `curak.xyz`.
7.  **Update DNS Records**:
    *   SendGrid will show you 3 CNAME records (e.g., `em1234.curak.xyz`).
    *   Go to your **DNS Provider** (where you manage `curak.xyz`).
    *   Add these 3 CNAME records exactly as shown.
8.  **Verify**:
    *   Go back to SendGrid and check the "I've added these records" box.
    *   Click **Verify**.
9.  **Update Environment**:
    *   Edit `/opt/deployment/repos/jobs/.env`
    *   Set `EMAIL_ADDRESS=noreply@curak.xyz` (or any name @curak.xyz).

## Option 3: The Alternative (Gmail App Password)
*If SendGrid is too annoying, you can switch back to standard Gmail SMTP.*

1.  Go to Google Account → Security.
2.  Enable **2-Step Verification**.
3.  Search for **App Passwords**.
4.  Create one named "Job Bot".
5.  Copy the 16-character code.
6.  Update `/opt/deployment/repos/jobs/.env`:
    ```ini
    EMAIL_ADDRESS=matusaltaner@gmail.com
    EMAIL_PASSWORD=your-16-char-app-password
    # Remove SMTP_USER or set it to your email
    ```
7.  Update `/opt/deployment/repos/jobs/config.yaml`:
    ```yaml
    email:
      smtp_server: "smtp.gmail.com"
      # ... other settings ...
    ```
