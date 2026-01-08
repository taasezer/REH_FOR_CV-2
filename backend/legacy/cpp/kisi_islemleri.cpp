#include <iostream>
#include <pqxx/pqxx>
#include <fstream>
#include <regex>

using namespace std;
using namespace pqxx;

bool validateEmail(const string& email) {
    const regex pattern(R"(^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$)");
    return regex_match(email, pattern);
}

void exportEmailsToFile(const string& filename = "emails_cpp.txt") {
    try {
        connection conn("host=db user=kullanici password=sifre dbname=rehber");
        work txn(conn);
        result res = txn.exec("SELECT eposta FROM kisi");

        ofstream file(filename);
        for (auto row : res) {
            string email = row[0].as<string>();
            if (validateEmail(email)) {
                file << email << endl;
            }
        }
        cout << "E-posta adresleri " << filename << " dosyasına aktarıldı." << endl;
    } catch (const exception &e) {
        cerr << "Hata: " << e.what() << endl;
    }
}

int main() {
    try {
        connection conn("host=db user=kullanici password=sifre dbname=rehber");

        work txn(conn);
        txn.exec(
            "INSERT INTO kisi (isim, eposta, telefon, adres) "
            "VALUES ('Mehmet Demir', 'mehmet@example.com', '5559876543', 'İstanbul, Türkiye')"
        );
        txn.commit();
        cout << "Kişi eklendi." << endl;

        exportEmailsToFile();
    } catch (const exception &e) {
        cerr << "Hata: " << e.what() << endl;
        return 1;
    }
    return 0;
}
