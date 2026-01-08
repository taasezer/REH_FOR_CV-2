FROM gcc:latest
WORKDIR /app
RUN apt-get update && apt-get install -y libpqxx-dev postgresql-client
COPY kisi_islemleri.cpp .
RUN g++ -std=c++11 kisi_islemleri.cpp -lpqxx -o kisi_islemleri
CMD ["./kisi_islemleri"]

