#!/bin/sh
set -e

# Path to the custom root certificate (assumed to be mounted into the container)
CUSTOM_CERT_PATH="/certs/custom_root.crt"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install certificate utilities if not present
install_cert_utilities() {
    echo "Checking for certificate utilities and package manager..."

    if command_exists apk; then
        PM="apk"
        INSTALL_CMD="apk add --no-cache"
        CERT_PACKAGE="ca-certificates ca-certificates-bundle openssl"

        echo "Using apk package manager."
        # Install ca-certificates package if not already installed
        $INSTALL_CMD $CERT_PACKAGE

    elif command_exists apt-get; then
        PM="apt-get"
        CERT_PACKAGE="ca-certificates openssl"

        echo "Using apt-get package manager."
        # Update package lists
        apt-get update
        # Install ca-certificates
        apt-get install -y $CERT_PACKAGE

    elif command_exists yum; then
        PM="yum"
        INSTALL_CMD="yum install -y"
        CERT_PACKAGE="ca-certificates openssl"

        echo "Using yum package manager."
        # Install ca-certificates
        $INSTALL_CMD $CERT_PACKAGE

    elif command_exists dnf; then
        PM="dnf"
        INSTALL_CMD="dnf install -y"
        CERT_PACKAGE="ca-certificates openssl"

        echo "Using dnf package manager."
        $INSTALL_CMD $CERT_PACKAGE

    elif command_exists zypper; then
        PM="zypper"
        INSTALL_CMD="zypper install -y"
        CERT_PACKAGE="ca-certificates openssl"

        echo "Using zypper package manager."
        $INSTALL_CMD $CERT_PACKAGE

    else
        echo "No supported package manager found. Cannot install certificate utilities."
        exit 1
    fi
}

# Install certificate utilities if not already installed
if ! command_exists update-ca-certificates && ! command_exists update-ca-trust; then
    install_cert_utilities
else
    echo "Certificate utilities already installed."
fi

# Copy the custom certificate into the appropriate directory and update trust store
update_trust_store() {
    echo "Updating trust store with custom certificate..."

    if [ -f /etc/alpine-release ]; then
        # Alpine Linux
        echo "Detected Alpine Linux."
        cp "$CUSTOM_CERT_PATH" /usr/local/share/ca-certificates/custom_root.crt
        update-ca-certificates

    elif [ -f /etc/debian_version ]; then
        # Debian/Ubuntu
        echo "Detected Debian/Ubuntu."
        cp "$CUSTOM_CERT_PATH" /usr/local/share/ca-certificates/custom_root.crt
        update-ca-certificates

    elif [ -f /etc/redhat-release ] || [ -f /etc/centos-release ]; then
        # RedHat/CentOS/Fedora
        echo "Detected RedHat/CentOS/Fedora."
        cp "$CUSTOM_CERT_PATH" /etc/pki/ca-trust/source/anchors/custom_root.crt
        update-ca-trust extract

    elif [ -f /etc/os-release ]; then
        OS_ID=$(grep '^ID=' /etc/os-release | cut -d'=' -f2 | tr -d '"')
        case "$OS_ID" in
            sles|opensuse*)
                echo "Detected SUSE Linux."
                cp "$CUSTOM_CERT_PATH" /etc/pki/trust/anchors/custom_root.crt
                update-ca-certificates
                ;;
            *)
                echo "Unsupported OS detected."
                exit 1
                ;;
        esac
    else
        echo "Cannot detect OS type. Exiting."
        exit 1
    fi
}

# Update the trust store
update_trust_store

# Check for common runtimes and configure them if needed

configure_java() {
    if command_exists java; then
        echo "Java runtime detected. Importing custom certificate into Java truststore."

        JAVA_HOME=$(dirname $(dirname $(readlink -f $(which java))))
        JAVA_CACERTS_PATH="$JAVA_HOME/lib/security/cacerts"
        if [ ! -f "$JAVA_CACERTS_PATH" ]; then
            echo "Java cacerts file not found at $JAVA_CACERTS_PATH. Skipping Java truststore update."
            return
        fi

        echo "Importing custom certificate into Java cacerts at $JAVA_CACERTS_PATH."
        yes | keytool -importcert -trustcacerts -alias custom_root -file "$CUSTOM_CERT_PATH" -keystore "$JAVA_CACERTS_PATH" -storepass changeit || true
    fi
}

configure_nodejs() {
    if command_exists node; then
        echo "Node.js runtime detected. Setting NODE_EXTRA_CA_CERTS environment variable."
        export NODE_EXTRA_CA_CERTS="$CUSTOM_CERT_PATH"
    fi
}

configure_python() {
    if command_exists python || command_exists python3; then
        echo "Python runtime detected. Setting SSL_CERT_FILE and REQUESTS_CA_BUNDLE environment variables."
        export SSL_CERT_FILE="$CUSTOM_CERT_PATH"
        export REQUESTS_CA_BUNDLE="$CUSTOM_CERT_PATH"
    fi
}

# Configure runtimes
configure_java
configure_nodejs
configure_python

# Ensure all environment variables are exported
export NODE_EXTRA_CA_CERTS
export SSL_CERT_FILE
export REQUESTS_CA_BUNDLE

# Log environment variables for debugging (optional)
echo "Environment variables set:"
#env | grep -E 'NODE_EXTRA_CA_CERTS|SSL_CERT_FILE|REQUESTS_CA_BUNDLE'

# Execute the original command
echo "Executing original command: $@"
exec "$@"
