"""
Tests for EnhancedGrpcGoParser.

Part of CodeTrellis v5.2 Go Framework Support.
Tests cover:
- Service implementation extraction (embedding Unimplemented*Server)
- RPC method extraction (unary, server stream, client stream, bidi stream)
- Interceptor extraction (unary server, stream server, unary client, stream client)
- Server options extraction (grpc.NewServer, grpc.Creds, MaxRecvMsgSize)
- Client connection extraction (grpc.Dial, grpc.DialContext, grpc.NewClient)
- Proto import extraction (google.golang.org/grpc)
- Framework detection
"""

import pytest
from codetrellis.grpc_go_parser_enhanced import (
    EnhancedGrpcGoParser,
    GrpcGoParseResult,
)


@pytest.fixture
def parser():
    return EnhancedGrpcGoParser()


SAMPLE_GRPC_SERVER = '''
package main

import (
    "context"
    "log"
    "net"

    "google.golang.org/grpc"
    "google.golang.org/grpc/credentials"
    "google.golang.org/grpc/reflection"
    "google.golang.org/grpc/health"
    "google.golang.org/grpc/health/grpc_health_v1"
    pb "myapp/proto/userpb"
)

type userServer struct {
    pb.UnimplementedUserServiceServer
    db *Database
}

func (s *userServer) GetUser(ctx context.Context, req *pb.GetUserRequest) (*pb.GetUserResponse, error) {
    user, err := s.db.FindUser(ctx, req.GetId())
    if err != nil {
        return nil, status.Errorf(codes.Internal, "lookup failed: %v", err)
    }
    return &pb.GetUserResponse{User: toProto(user)}, nil
}

func (s *userServer) ListUsers(req *pb.ListUsersRequest, stream pb.UserService_ListUsersServer) error {
    users, _ := s.db.AllUsers(stream.Context())
    for _, u := range users {
        if err := stream.Send(toProto(u)); err != nil {
            return err
        }
    }
    return nil
}

func (s *userServer) CreateUsers(stream pb.UserService_CreateUsersServer) error {
    for {
        req, err := stream.Recv()
        if err == io.EOF {
            return stream.SendAndClose(&pb.CreateUsersResponse{Count: count})
        }
        if err != nil {
            return err
        }
        // process
    }
}

func (s *userServer) Chat(stream pb.UserService_ChatServer) error {
    for {
        msg, err := stream.Recv()
        if err == io.EOF {
            return nil
        }
        stream.Send(&pb.ChatResponse{Message: "ack"})
    }
}

type orderServer struct {
    pb.UnimplementedOrderServiceServer
}

func (s *orderServer) GetOrder(ctx context.Context, req *pb.GetOrderRequest) (*pb.GetOrderResponse, error) {
    return &pb.GetOrderResponse{}, nil
}

func loggingInterceptor(ctx context.Context, req interface{}, info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (interface{}, error) {
    log.Printf("gRPC call: %s", info.FullMethod)
    return handler(ctx, req)
}

func streamLoggingInterceptor(srv interface{}, ss grpc.ServerStream, info *grpc.StreamServerInfo, handler grpc.StreamHandler) error {
    log.Printf("gRPC stream: %s", info.FullMethod)
    return handler(srv, ss)
}

func main() {
    creds, _ := credentials.NewServerTLSFromFile("cert.pem", "key.pem")

    srv := grpc.NewServer(
        grpc.Creds(creds),
        grpc.ChainUnaryInterceptor(loggingInterceptor),
        grpc.ChainStreamInterceptor(streamLoggingInterceptor),
        grpc.MaxRecvMsgSize(10 * 1024 * 1024),
    )

    pb.RegisterUserServiceServer(srv, &userServer{})
    pb.RegisterOrderServiceServer(srv, &orderServer{})

    reflection.Register(srv)
    healthSrv := health.NewServer()
    grpc_health_v1.RegisterHealthServer(srv, healthSrv)

    lis, _ := net.Listen("tcp", ":50051")
    srv.Serve(lis)
}
'''

SAMPLE_GRPC_CLIENT = '''
package main

import (
    "google.golang.org/grpc"
    "google.golang.org/grpc/credentials/insecure"
    "google.golang.org/grpc/metadata"
    pb "myapp/proto/userpb"
)

func main() {
    conn, err := grpc.Dial("localhost:50051",
        grpc.WithTransportCredentials(insecure.NewCredentials()),
    )
    if err != nil {
        log.Fatal(err)
    }
    defer conn.Close()

    client := pb.NewUserServiceClient(conn)

    md := metadata.Pairs("authorization", "Bearer token123")
    ctx := metadata.NewOutgoingContext(context.Background(), md)

    resp, err := client.GetUser(ctx, &pb.GetUserRequest{Id: "123"})
}
'''


class TestGrpcGoParser:

    def test_parse_returns_result(self, parser):
        result = parser.parse(SAMPLE_GRPC_SERVER, "server.go")
        assert isinstance(result, GrpcGoParseResult)

    def test_detect_grpc_framework(self, parser):
        result = parser.parse(SAMPLE_GRPC_SERVER, "server.go")
        assert len(result.detected_frameworks) > 0
        assert "grpc" in result.detected_frameworks

    def test_extract_service_impls(self, parser):
        result = parser.parse(SAMPLE_GRPC_SERVER, "server.go")
        assert len(result.service_impls) >= 2
        names = [s.name for s in result.service_impls]
        assert any("userServer" in n or "user" in n.lower() for n in names)

    def test_extract_rpc_methods(self, parser):
        result = parser.parse(SAMPLE_GRPC_SERVER, "server.go")
        assert len(result.rpc_methods) >= 3

    def test_extract_interceptors(self, parser):
        result = parser.parse(SAMPLE_GRPC_SERVER, "server.go")
        assert len(result.interceptors) >= 1

    def test_extract_server_options(self, parser):
        result = parser.parse(SAMPLE_GRPC_SERVER, "server.go")
        assert len(result.server_options) >= 1

    def test_extract_client_connections(self, parser):
        result = parser.parse(SAMPLE_GRPC_CLIENT, "client.go")
        assert len(result.client_connections) >= 1

    def test_extract_proto_imports(self, parser):
        result = parser.parse(SAMPLE_GRPC_SERVER, "server.go")
        assert len(result.proto_imports) >= 1

    def test_non_grpc_file(self, parser):
        result = parser.parse("package main\n\nfunc main() {}", "main.go")
        assert len(result.service_impls) == 0
        assert len(result.detected_frameworks) == 0

    def test_grpc_detection(self, parser):
        result = parser.parse(SAMPLE_GRPC_SERVER, "server.go")
        assert len(result.detected_frameworks) > 0
        result2 = parser.parse("package main\nfunc main() {}", "main.go")
        assert len(result2.detected_frameworks) == 0
