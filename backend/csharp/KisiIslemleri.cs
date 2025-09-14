using System;
using System.IO;
using System.Text.RegularExpressions;
using Npgsql;

public class KisiIslemleri
{
    private static string connectionString = "Host=db;Username=kullanici;Password=sifre;Database=rehber";

    public static bool ValidateEmail(string email)
    {
        string pattern = @"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$";
        Regex regex = new Regex(pattern);
        return regex.IsMatch(email);
    }

    public static void KisiEkle(string isim, string eposta, string telefon, string adres)
    {
        using (var connection = new NpgsqlConnection(connectionString))
        {
            connection.Open();
            var command = new NpgsqlCommand(
                "INSERT INTO kisi (isim, eposta, telefon, adres) VALUES (@isim, @eposta, @telefon, @adres)",
                connection
            );
            command.Parameters.AddWithValue("@isim", isim);
            command.Parameters.AddWithValue("@eposta", eposta);
            command.Parameters.AddWithValue("@telefon", telefon);
            command.Parameters.AddWithValue("@adres", adres);
            command.ExecuteNonQuery();
            Console.WriteLine("Kişi eklendi.");
        }
    }

    public static void ExportEmailsToFile(string filename = "emails_csharp.txt")
    {
        using (var connection = new NpgsqlConnection(connectionString))
        {
            connection.Open();
            var command = new NpgsqlCommand("SELECT eposta FROM kisi", connection);
            using (var reader = command.ExecuteReader())
            {
                using (StreamWriter file = new StreamWriter(filename))
                {
                    while (reader.Read())
                    {
                        string email = reader.GetString(0);
                        if (ValidateEmail(email))
                        {
                            file.WriteLine(email);
                        }
                    }
                }
            }
            Console.WriteLine($"E-posta adresleri {filename} dosyasına aktarıldı.");
        }
    }

    public static void Main(string[] args)
    {
        KisiEkle("Ahmet Yılmaz", "ahmet@example.com", "5551234567", "Ankara, Türkiye");
        ExportEmailsToFile();
    }
}
