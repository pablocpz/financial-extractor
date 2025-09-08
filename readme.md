# Reports Field Extractor

Takes in all the reports in a given folder and export a extracted aggregated data into an excel in another given out folder


## Build
```bash
docker build -t reports-processor .

or with Compose:

docker compose build

Run

Without Docker

python main.py reports out

With Docker

docker run --rm \
  -v "$PWD/reports:/reports" \
  -v "$PWD/out:/out" \
  reports-processor /reports /out

With Docker Compose

docker compose up --build

Structure

main.py            # entry point
requirements.txt   # dependencies
Dockerfile
compose.yaml
reports/           # input
out/               # output