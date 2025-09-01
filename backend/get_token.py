from google_auth_oauthlib.flow import InstalledAppFlow

# Datos de tu app (desde Google Cloud Console)
CLIENT_ID = "380799892504-ftc1iphldrc5v2c6sd8f2dupjjodt04a.apps.googleusercontent.com"
CLIENT_SECRET = "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"

SCOPES = ["https://mail.google.com/"]

flow = InstalledAppFlow.from_client_config(
    {
        "installed": {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uris": ["https://apigc.ayltispa.com"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    },
    SCOPES,
)

# Esto abre un navegador en http://localhost:8080 para autenticar
creds = flow.run_local_server(port=0)

print("Access Token:", creds.token)
print("Refresh Token:", creds.refresh_token)
print("Token URI:", creds.token_uri)
