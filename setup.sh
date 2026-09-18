mkdir -p ~/.streamlit

cat > ~/.streamlit/config.toml <<EOF
[server]
headless = true
enableCORS = false
enableXsrfProtection = false

[theme]
base = "dark"
primaryColor = "#E8B23B"
backgroundColor = "#0D1017"
secondaryBackgroundColor = "#11131A"
textColor = "#ffffff"
font = "sans serif"
EOF
