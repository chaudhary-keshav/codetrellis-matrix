"""
Tests for EnhancedCobraParser.

Part of CodeTrellis v5.2 Go Framework Support.
Tests cover:
- Command extraction (cobra.Command{} definitions)
- Flag extraction (PersistentFlags, Flags, types)
- Sub-command extraction (AddCommand)
- Group extraction (AddGroup)
- Viper binding extraction (BindPFlag, BindEnv)
- Root command detection
- Framework detection
"""

import pytest
from codetrellis.cobra_parser_enhanced import (
    EnhancedCobraParser,
    CobraParseResult,
)


@pytest.fixture
def parser():
    return EnhancedCobraParser()


SAMPLE_COBRA_APP = '''
package cmd

import (
    "fmt"
    "os"

    "github.com/spf13/cobra"
    "github.com/spf13/viper"
)

var cfgFile string

var rootCmd = &cobra.Command{
    Use:   "myapp",
    Short: "My application for managing things",
    Long:  `A longer description of myapp that spans multiple lines.`,
    PersistentPreRunE: func(cmd *cobra.Command, args []string) error {
        return initConfig()
    },
}

var serveCmd = &cobra.Command{
    Use:   "serve",
    Short: "Start the HTTP server",
    Long:  "Start the HTTP server with the specified port and configuration.",
    RunE: func(cmd *cobra.Command, args []string) error {
        port, _ := cmd.Flags().GetInt("port")
        return startServer(port)
    },
}

var migrateCmd = &cobra.Command{
    Use:   "migrate",
    Short: "Run database migrations",
    Args:  cobra.ExactArgs(1),
    ValidArgs: []string{"up", "down", "status"},
    Run: func(cmd *cobra.Command, args []string) {
        runMigration(args[0])
    },
}

var versionCmd = &cobra.Command{
    Use:   "version",
    Short: "Print version information",
    Run: func(cmd *cobra.Command, args []string) {
        fmt.Println("v1.0.0")
    },
}

var deployCmd = &cobra.Command{
    Use:   "deploy [environment]",
    Short: "Deploy the application",
    Args:  cobra.ExactArgs(1),
    RunE:  runDeploy,
}

func init() {
    rootCmd.PersistentFlags().StringVar(&cfgFile, "config", "", "config file (default is $HOME/.myapp.yaml)")
    rootCmd.PersistentFlags().BoolP("verbose", "v", false, "verbose output")
    rootCmd.PersistentFlags().String("log-level", "info", "log level (debug, info, warn, error)")

    serveCmd.Flags().IntP("port", "p", 8080, "server port")
    serveCmd.Flags().Bool("tls", false, "enable TLS")
    serveCmd.MarkFlagRequired("port")

    migrateCmd.Flags().String("dsn", "", "database connection string")
    migrateCmd.MarkFlagRequired("dsn")

    deployCmd.Flags().StringP("region", "r", "us-east-1", "deployment region")
    deployCmd.Flags().Int("replicas", 3, "number of replicas")

    viper.BindPFlag("log_level", rootCmd.PersistentFlags().Lookup("log-level"))
    viper.BindPFlag("verbose", rootCmd.PersistentFlags().Lookup("verbose"))
    viper.BindEnv("database_url", "DATABASE_URL")
    viper.SetEnvPrefix("MYAPP")
    viper.AutomaticEnv()

    rootCmd.AddCommand(serveCmd)
    rootCmd.AddCommand(migrateCmd)
    rootCmd.AddCommand(versionCmd)
    rootCmd.AddCommand(deployCmd)

    rootCmd.AddGroup(&cobra.Group{ID: "server", Title: "Server Commands:"})
    rootCmd.AddGroup(&cobra.Group{ID: "db", Title: "Database Commands:"})
    serveCmd.GroupID = "server"
    migrateCmd.GroupID = "db"
}

func Execute() {
    if err := rootCmd.Execute(); err != nil {
        os.Exit(1)
    }
}
'''


class TestCobraParser:

    def test_parse_returns_result(self, parser):
        result = parser.parse(SAMPLE_COBRA_APP, "root.go")
        assert isinstance(result, CobraParseResult)

    def test_detect_cobra_framework(self, parser):
        result = parser.parse(SAMPLE_COBRA_APP, "root.go")
        assert len(result.detected_frameworks) > 0
        assert "cobra" in result.detected_frameworks

    def test_extract_commands(self, parser):
        result = parser.parse(SAMPLE_COBRA_APP, "root.go")
        assert len(result.commands) >= 4
        uses = [c.use for c in result.commands]
        assert any("serve" in u for u in uses)
        assert any("migrate" in u for u in uses)

    def test_extract_flags(self, parser):
        result = parser.parse(SAMPLE_COBRA_APP, "root.go")
        assert len(result.flags) >= 4
        names = [f.name for f in result.flags]
        assert any("config" in n for n in names)
        assert any("port" in n for n in names)

    def test_extract_sub_commands(self, parser):
        result = parser.parse(SAMPLE_COBRA_APP, "root.go")
        assert len(result.sub_commands) >= 3
        children = [s.child for s in result.sub_commands]
        assert any("serve" in c.lower() for c in children)

    def test_extract_groups(self, parser):
        result = parser.parse(SAMPLE_COBRA_APP, "root.go")
        assert len(result.groups) >= 1

    def test_extract_viper_bindings(self, parser):
        result = parser.parse(SAMPLE_COBRA_APP, "root.go")
        assert len(result.viper_bindings) >= 1

    def test_non_cobra_file(self, parser):
        result = parser.parse("package main\n\nfunc main() {}", "main.go")
        assert len(result.commands) == 0
        assert len(result.detected_frameworks) == 0

    def test_cobra_detection(self, parser):
        result = parser.parse(SAMPLE_COBRA_APP, "root.go")
        assert len(result.detected_frameworks) > 0
        result2 = parser.parse("package main\nfunc main() {}", "main.go")
        assert len(result2.detected_frameworks) == 0
