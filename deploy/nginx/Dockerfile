FROM nginx:1.27-alpine

# Build-time self-signed certificate for the TLS demo listener. This is a
# throwaway LAB cert generated inside the image -- the private key is never
# committed to the repo and never leaves the container.
RUN apk add --no-cache openssl \
    && mkdir -p /etc/nginx/certs \
    && openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
        -keyout /etc/nginx/certs/lab.key \
        -out /etc/nginx/certs/lab.crt \
        -subj "/CN=localhost" \
    && chmod 600 /etc/nginx/certs/lab.key

COPY nginx.conf /etc/nginx/nginx.conf
COPY app_proxy.conf /etc/nginx/app_proxy.conf

EXPOSE 80 443
