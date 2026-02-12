# ---- Stage 1: Builder ----
FROM python:3.12-slim AS builder

WORKDIR /build

COPY pyproject.toml .
COPY course_factory/ course_factory/

RUN pip install --no-cache-dir .

# ---- Stage 2: Runtime ----
FROM python:3.12-slim AS runtime

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/cf /usr/local/bin/cf
COPY course_factory/ course_factory/

EXPOSE 8000 8080

ENV CF_LOG_LEVEL=INFO

ENTRYPOINT ["cf"]
CMD ["version"]
