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

# Wine runs the official 32-bit x86 MUGEN tools (sprmake2.exe, sff2png.exe)
# mounted at /mugen. Wine 9+'s new WoW64 mode executes 32-bit PE without needing
# 32-bit host libraries, which is what lets it work on musl/Alpine. wine lives in
# the community repository.
RUN apk add --no-cache --repository=https://dl-cdn.alpinelinux.org/alpine/edge/community \
        wine

# Wine needs a writable HOME + prefix. WINEDEBUG silences its verbose logging.
# WINEARCH=win64 is a 64-bit prefix; WoW64 still runs the 32-bit tools inside it.
# XDG_RUNTIME_DIR is set to a private dir so Wine doesn't warn about it.
ENV HOME=/root \
    WINEPREFIX=/root/.wine \
    WINEARCH=win64 \
    WINEDEBUG=-all \
    XDG_RUNTIME_DIR=/run/user-wine
# Initialize the Wine prefix at build time so the first conversion isn't slow.
RUN mkdir -p "$XDG_RUNTIME_DIR" && chmod 700 "$XDG_RUNTIME_DIR" \
    && wineboot --init && wineserver -w

# Application binaries live here...
COPY --from=build /app /opt/fm2ndparser

# ...and /data is where you mount the FM2nd game files to parse.
WORKDIR /data

ENTRYPOINT ["dotnet", "/opt/fm2ndparser/Fm2ndParser.dll"]
CMD ["--help"]
