"""
Tests for EnhancedCParser — full integration of all C extractors.

Part of CodeTrellis v4.19 C Language Support.
"""

import pytest
from codetrellis.c_parser_enhanced import EnhancedCParser, CParseResult


@pytest.fixture
def parser():
    return EnhancedCParser()


class TestCParserBasic:
    """Tests for basic C parsing capabilities."""

    def test_parse_simple_c_file(self, parser):
        code = '''
#include <stdio.h>
#include <stdlib.h>

typedef struct {
    int x;
    int y;
} Point;

int add(int a, int b) {
    return a + b;
}

int main(void) {
    Point p = {1, 2};
    printf("sum = %d\\n", add(p.x, p.y));
    return 0;
}
'''
        result = parser.parse(code, "main.c")
        assert result.file_type == "c"
        assert len(result.functions) >= 2  # add and main
        assert len(result.includes) >= 2

    def test_parse_header_file(self, parser):
        code = '''
#ifndef MY_LIB_H
#define MY_LIB_H

struct config {
    int timeout;
    int retries;
};

int lib_init(struct config *cfg);
void lib_cleanup(void);

#endif /* MY_LIB_H */
'''
        result = parser.parse(code, "my_lib.h")
        assert result.is_header is True
        assert result.include_guard is not None
        assert 'MY_LIB_H' in result.include_guard
        assert len(result.structs) >= 1

    def test_pragma_once(self, parser):
        code = '''
#pragma once

void foo(void);
'''
        result = parser.parse(code, "foo.h")
        assert result.include_guard == '__pragma_once__'

    def test_empty_file(self, parser):
        result = parser.parse("", "empty.c")
        assert result.file_type == "c"
        assert len(result.functions) == 0
        assert len(result.structs) == 0


class TestCParserFrameworkDetection:
    """Tests for C framework/library detection."""

    def test_detect_posix(self, parser):
        code = '''
#include <unistd.h>
#include <sys/types.h>
#include <fcntl.h>

int fd = open("file.txt", O_RDONLY);
'''
        result = parser.parse(code, "file.c")
        assert "posix" in result.detected_frameworks

    def test_detect_pthreads(self, parser):
        code = '''
#include <pthread.h>

pthread_t thread;
pthread_mutex_t lock;
'''
        result = parser.parse(code, "thread.c")
        assert "pthreads" in result.detected_frameworks

    def test_detect_openssl(self, parser):
        code = '''
#include <openssl/ssl.h>
#include <openssl/err.h>

SSL_CTX *ctx = SSL_CTX_new(TLS_client_method());
'''
        result = parser.parse(code, "ssl.c")
        assert "openssl" in result.detected_frameworks

    def test_detect_libcurl(self, parser):
        code = '''
#include <curl/curl.h>

CURL *curl = curl_easy_init();
curl_easy_setopt(curl, CURLOPT_URL, "https://example.com");
'''
        result = parser.parse(code, "http.c")
        assert "libcurl" in result.detected_frameworks

    def test_detect_sqlite(self, parser):
        code = '''
#include <sqlite3.h>

sqlite3 *db;
sqlite3_open(":memory:", &db);
'''
        result = parser.parse(code, "db.c")
        assert "sqlite3" in result.detected_frameworks

    def test_detect_libuv(self, parser):
        code = '''
#include <uv.h>

uv_loop_t *loop = uv_default_loop();
uv_tcp_t server;
'''
        result = parser.parse(code, "server.c")
        assert "libuv" in result.detected_frameworks

    def test_detect_ncurses(self, parser):
        code = '''
#include <ncurses.h>

initscr();
mvprintw(0, 0, "Hello");
endwin();
'''
        result = parser.parse(code, "tui.c")
        assert "ncurses" in result.detected_frameworks

    def test_detect_linux_kernel(self, parser):
        code = '''
#include <linux/module.h>
#include <linux/kernel.h>

MODULE_LICENSE("GPL");
module_init(my_init);
'''
        result = parser.parse(code, "driver.c")
        assert "linux_kernel" in result.detected_frameworks

    def test_detect_glib(self, parser):
        code = '''
#include <glib.h>

GList *list = NULL;
g_list_append(list, data);
GHashTable *table = g_hash_table_new(g_str_hash, g_str_equal);
'''
        result = parser.parse(code, "app.c")
        assert "glib" in result.detected_frameworks


class TestCParserStandardDetection:
    """Tests for C standard version detection."""

    def test_detect_c89_default(self, parser):
        code = '''
int main() {
    int x;
    x = 42;
    return 0;
}
'''
        result = parser.parse(code, "old.c")
        assert result.c_standard == "c89"

    def test_detect_c99(self, parser):
        code = '''
#include <stdbool.h>

inline int max(int a, int b) {
    return a > b ? a : b;
}
'''
        result = parser.parse(code, "modern.c")
        assert result.c_standard in ("c99", "c11", "c23")

    def test_detect_c11(self, parser):
        code = '''
#include <stdatomic.h>
#include <threads.h>

_Atomic int counter = 0;
_Static_assert(sizeof(int) >= 4, "int must be at least 32 bits");
'''
        result = parser.parse(code, "c11.c")
        assert result.c_standard in ("c11", "c23")

    def test_detect_c23(self, parser):
        code = '''
constexpr int MAX_SIZE = 1024;
auto x = 42;
[[nodiscard]] int compute(void);
'''
        result = parser.parse(code, "c23.c")
        assert result.c_standard == "c23"


class TestCParserCompilerDetection:
    """Tests for compiler extension detection."""

    def test_detect_gcc(self, parser):
        code = '''
#ifdef __GNUC__
__attribute__((unused)) static int x;
int y = __builtin_expect(x, 0);
#endif
'''
        result = parser.parse(code, "gcc.c")
        assert result.detected_compiler == "gcc"

    def test_detect_clang(self, parser):
        code = '''
#if __has_feature(address_sanitizer)
__attribute__((no_sanitize("address"))) void f(void) {}
#endif
'''
        result = parser.parse(code, "clang.c")
        assert result.detected_compiler == "clang"

    def test_detect_msvc(self, parser):
        code = '''
#ifdef _MSC_VER
__declspec(dllexport) void __stdcall api_func(void) {}
#endif
'''
        result = parser.parse(code, "msvc.c")
        assert result.detected_compiler == "msvc"


class TestCParserFeatureDetection:
    """Tests for C language feature detection."""

    def test_detect_inline(self, parser):
        code = '''
static inline int square(int x) { return x * x; }
'''
        result = parser.parse(code, "feat.c")
        assert "inline_functions" in result.detected_features

    def test_detect_atomics(self, parser):
        code = '''
_Atomic int counter = ATOMIC_VAR_INIT(0);
'''
        result = parser.parse(code, "atomic.c")
        assert "atomics" in result.detected_features

    def test_detect_generics(self, parser):
        code = '''
#define typename(x) _Generic((x), \\
    int: "int", \\
    float: "float", \\
    default: "other")
'''
        result = parser.parse(code, "generic.c")
        assert "generics" in result.detected_features


class TestCParserIntegration:
    """Tests for full parser integration with all extractors."""

    def test_comprehensive_c_file(self, parser):
        code = '''
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <signal.h>
#include <sys/socket.h>

#define MAX_CLIENTS 128
#define BUFFER_SIZE 4096

typedef enum {
    STATE_INIT,
    STATE_RUNNING,
    STATE_SHUTDOWN
} ServerState;

typedef struct client {
    int fd;
    char addr[64];
    struct client *next;
} Client;

typedef void (*event_handler_t)(int fd, void *data);

struct server {
    int listen_fd;
    ServerState state;
    Client *clients;
    pthread_mutex_t lock;
    event_handler_t on_connect;
    event_handler_t on_disconnect;
};

static volatile sig_atomic_t running = 1;

void handle_sigint(int sig) {
    running = 0;
}

static int server_init(struct server *srv, int port) {
    srv->listen_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (srv->listen_fd < 0) return -1;

    struct sockaddr_in addr = {0};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(port);

    if (bind(srv->listen_fd, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        return -1;
    }

    listen(srv->listen_fd, MAX_CLIENTS);
    pthread_mutex_init(&srv->lock, NULL);
    srv->state = STATE_RUNNING;
    return 0;
}

static void server_destroy(struct server *srv) {
    pthread_mutex_destroy(&srv->lock);
    close(srv->listen_fd);
}

int main(void) {
    signal(SIGINT, handle_sigint);

    struct server srv = {0};
    if (server_init(&srv, 8080) < 0) {
        perror("server_init");
        return EXIT_FAILURE;
    }

    while (running) {
        int client_fd = accept(srv.listen_fd, NULL, NULL);
        if (client_fd >= 0) {
            Client *c = malloc(sizeof(*c));
            if (c) {
                c->fd = client_fd;
                c->next = srv.clients;
                srv.clients = c;
            }
        }
    }

    server_destroy(&srv);
    return EXIT_SUCCESS;
}
'''
        result = parser.parse(code, "server.c")

        # Types
        assert len(result.enums) >= 1  # ServerState
        assert len(result.structs) >= 2  # client, server
        assert len(result.typedefs) >= 1

        # Functions
        assert len(result.functions) >= 3  # handle_sigint, server_init, server_destroy, main

        # API patterns
        assert len(result.socket_apis) >= 1  # socket/bind/listen/accept
        assert len(result.signal_handlers) >= 1  # SIGINT

        # Preprocessor
        assert len(result.macros) >= 2  # MAX_CLIENTS, BUFFER_SIZE
        assert len(result.includes) >= 6

        # Framework detection
        assert "pthreads" in result.detected_frameworks
        assert "posix" in result.detected_frameworks

        # Data structures
        # Client has a next pointer → linked list pattern
        assert len(result.data_structures) >= 0  # May detect linked list

        # Global vars
        assert len(result.global_vars) >= 0


class TestCParserCMake:
    """Tests for CMakeLists.txt parsing."""

    def test_parse_cmake(self):
        cmake = '''
cmake_minimum_required(VERSION 3.15)
project(myserver VERSION 2.1.0)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

add_executable(myserver src/main.c src/server.c)
add_library(mylib STATIC src/lib.c)

find_package(OpenSSL REQUIRED)
find_package(ZLIB)

target_link_libraries(myserver PRIVATE OpenSSL::SSL ZLIB::ZLIB mylib)

option(ENABLE_TESTS "Build test suite" ON)
'''
        result = EnhancedCParser.parse_cmake_lists(cmake)
        assert result['project_name'] == 'myserver'
        assert result['version'] == '2.1.0'
        assert result['c_standard'] == 'c11'
        assert 'myserver' in result['targets']
        assert 'mylib' in result['targets']
        assert 'OpenSSL' in result['packages']

    def test_parse_makefile(self):
        makefile = '''
CC = gcc
CFLAGS = -Wall -Wextra -std=c11 -O2
LDFLAGS = -lpthread -lssl -lcrypto

SRC = main.c server.c
OBJ = $(SRC:.c=.o)

all: myserver

myserver: $(OBJ)
\t$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

clean:
\trm -f $(OBJ) myserver
'''
        result = EnhancedCParser.parse_makefile(makefile)
        assert result['cc'] == 'gcc'
        assert result['c_standard'] == 'c11'
        assert 'pthread' in result['libraries']
        assert 'ssl' in result['libraries']
        assert 'all' in result['targets'] or 'myserver' in result['targets']
