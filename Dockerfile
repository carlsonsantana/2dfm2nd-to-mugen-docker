# ---- Build stage: full .NET 10 SDK on Alpine ----
FROM mcr.microsoft.com/dotnet/sdk:10.0-alpine AS build
WORKDIR /src

# Restore first (leverages Docker layer caching for dependencies)
COPY fm2ndparser/Fm2ndParser/Fm2ndParser.csproj Fm2ndParser/
RUN dotnet restore Fm2ndParser/Fm2ndParser.csproj

# Copy the rest of the sources and publish a Release build
COPY fm2ndparser .
RUN dotnet publish Fm2ndParser/Fm2ndParser.csproj \
        -c Release \
        -o /app \
        --no-restore

# ---- Runtime stage: slim .NET 10 runtime on Alpine ----
FROM mcr.microsoft.com/dotnet/runtime:10.0-alpine AS runtime

# Application binaries live here...
COPY --from=build /app /opt/fm2ndparser

# ...and /data is where you mount the FM2nd game files to parse.
WORKDIR /data

ENTRYPOINT ["dotnet", "/opt/fm2ndparser/Fm2ndParser.dll"]
CMD ["--help"]
