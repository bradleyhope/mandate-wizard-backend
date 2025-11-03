# Mandate Wizard V5 - Deployment Guide

This guide provides instructions for deploying the Mandate Wizard V5 application to a production environment.

---

## Deployment Options

### Option 1: Gunicorn (Recommended)

Gunicorn is a mature, widely-used WSGI HTTP server for UNIX. It's a pre-fork worker model, meaning a master process manages a number of worker processes.

1.  **Install Gunicorn:**

    ```bash
    pip install gunicorn
    ```

2.  **Run the application with Gunicorn:**

    ```bash
    gunicorn -w 4 -b 0.0.0.0:5000 app:app
    ```

    -   `-w 4`: Specifies 4 worker processes. Adjust based on your server's CPU cores (a common recommendation is `2 * num_cores + 1`).
    -   `-b 0.0.0.0:5000`: Binds the application to port 5000 on all network interfaces.

### Option 2: Docker

Docker allows you to package the application and its dependencies into a standardized unit for software development.

1.  **Create a `Dockerfile`:**

    ```dockerfile
    FROM python:3.11-slim

    WORKDIR /app

    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt

    COPY . .

    ENV PINECONE_API_KEY your_pinecone_api_key
    ENV PINECONE_INDEX_NAME your_pinecone_index_name
    ENV NEO4J_URI your_neo4j_uri
    ENV NEO4J_USER your_neo4j_user
    ENV NEO4J_PASSWORD your_neo4j_password
    ENV OPENAI_API_KEY your_openai_api_key

    EXPOSE 5000

    CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
    ```

2.  **Build the Docker image:**

    ```bash
    docker build -t mandate-wizard-v5 .
    ```

3.  **Run the Docker container:**

    ```bash
    docker run -p 5000:5000 mandate-wizard-v5
    ```

### Option 3: Cloud Platforms (Heroku, AWS, etc.)

Mandate Wizard can be deployed to any major cloud platform that supports Python applications.

-   **Heroku:** Use a `Procfile` to specify the Gunicorn command.
-   **AWS Elastic Beanstalk:** Configure the environment to use a WSGI server like Gunicorn.
-   **Google App Engine:** Use the `app.yaml` configuration to define the runtime and entrypoint.

In all cases, ensure you set the required environment variables in your cloud platform's configuration settings.

---

## Production Best Practices

### Environment Variables

**Never** hard-code API keys or other sensitive information in your code. Use environment variables to manage configuration.

### Reverse Proxy (Nginx)

In a production environment, it's recommended to run Gunicorn behind a reverse proxy like Nginx. Nginx can handle tasks like:

-   Terminating SSL/TLS (HTTPS)
-   Serving static files directly
-   Load balancing (if you have multiple application servers)
-   Buffering slow clients

### Logging and Monitoring

-   **Application Logging:** Configure Gunicorn to write logs to a file. Use a centralized logging service (e.g., ELK stack, Splunk, Datadog) to aggregate and analyze logs.
-   **Performance Monitoring:** Use a tool like Prometheus, Grafana, or a commercial APM (Application Performance Management) solution to monitor application performance, error rates, and resource usage.

---

*This guide provides a starting point for deploying Mandate Wizard V5. Adapt the configurations to your specific infrastructure and security requirements.*
