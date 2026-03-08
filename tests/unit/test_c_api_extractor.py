"""
Tests for C API extractor — sockets, signals, IPC, callbacks, threading.

Part of CodeTrellis v4.19 C Language Support.
"""

import pytest
from codetrellis.extractors.c.api_extractor import (
    CAPIExtractor, CSocketAPIInfo, CSignalHandlerInfo, CIPCInfo, CCallbackInfo,
)


@pytest.fixture
def extractor():
    return CAPIExtractor()


class TestCSocketAPIExtraction:
    """Tests for C socket API extraction."""

    def test_basic_socket_server(self, extractor):
        code = '''
int server_fd = socket(AF_INET, SOCK_STREAM, 0);
bind(server_fd, (struct sockaddr *)&addr, sizeof(addr));
listen(server_fd, 10);
int client_fd = accept(server_fd, NULL, NULL);
'''
        result = extractor.extract(code)
        assert len(result['socket_apis']) >= 1

    def test_udp_socket(self, extractor):
        code = '''
int sock = socket(AF_INET, SOCK_DGRAM, 0);
sendto(sock, buf, len, 0, (struct sockaddr *)&dest, sizeof(dest));
recvfrom(sock, buf, sizeof(buf), 0, NULL, NULL);
'''
        result = extractor.extract(code)
        assert len(result['socket_apis']) >= 1

    def test_epoll_detection(self, extractor):
        code = '''
int epfd = epoll_create1(0);
struct epoll_event ev;
ev.events = EPOLLIN | EPOLLET;
epoll_ctl(epfd, EPOLL_CTL_ADD, fd, &ev);
int n = epoll_wait(epfd, events, MAX_EVENTS, -1);
'''
        result = extractor.extract(code)
        assert len(result['socket_apis']) >= 1


class TestCSignalHandlerExtraction:
    """Tests for C signal handler extraction."""

    def test_signal_handler(self, extractor):
        code = '''
void handle_sigint(int sig) {
    running = 0;
}
signal(SIGINT, handle_sigint);
'''
        result = extractor.extract(code)
        assert len(result['signal_handlers']) >= 1

    def test_sigaction_handler(self, extractor):
        code = '''
struct sigaction sa;
sa.sa_handler = cleanup;
sigemptyset(&sa.sa_mask);
sa.sa_flags = 0;
sigaction(SIGTERM, &sa, NULL);
'''
        result = extractor.extract(code)
        assert len(result['signal_handlers']) >= 1


class TestCIPCExtraction:
    """Tests for C IPC extraction."""

    def test_pipe_detection(self, extractor):
        code = '''
int pipefd[2];
pipe(pipefd);
write(pipefd[1], "hello", 5);
'''
        result = extractor.extract(code)
        assert len(result['ipc']) >= 1

    def test_mmap_detection(self, extractor):
        code = '''
void *ptr = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
munmap(ptr, size);
'''
        result = extractor.extract(code)
        assert len(result['ipc']) >= 1

    def test_semaphore_detection(self, extractor):
        code = '''
sem_t *sem = sem_open("/mysem", O_CREAT, 0644, 1);
sem_wait(sem);
sem_post(sem);
'''
        result = extractor.extract(code)
        assert len(result['ipc']) >= 1


class TestCCallbackExtraction:
    """Tests for C callback extraction."""

    def test_callback_parameter(self, extractor):
        code = '''
void register_handler(void (*callback)(int event, void *data), void *ctx) {
    handler = callback;
    handler_ctx = ctx;
}
'''
        result = extractor.extract(code)
        assert len(result['callbacks']) >= 1


class TestCThreadingDetection:
    """Tests for C threading API detection."""

    def test_pthread_detection(self, extractor):
        code = '''
#include <pthread.h>
pthread_t thread;
pthread_create(&thread, NULL, worker, NULL);
pthread_mutex_lock(&lock);
pthread_mutex_unlock(&lock);
pthread_join(thread, NULL);
'''
        result = extractor.extract(code)
        assert len(result['threading']) >= 1
