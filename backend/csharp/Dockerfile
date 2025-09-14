FROM mcr.microsoft.com/dotnet/sdk:6.0
WORKDIR /app
COPY . .
RUN dotnet publish -c Release -o out
ENTRYPOINT ["dotnet", "out/KisiIslemleri.dll"]
