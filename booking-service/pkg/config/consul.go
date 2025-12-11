package config

import (
	"bytes"
	"context"
	"fmt"
	"path/filepath"

	"github.com/hashicorp/consul/api"
	"github.com/spf13/viper"
	"golang.org/x/sync/errgroup"
)

// ConsulConfigLoader loads config from Consul KV
type ConsulConfigLoader struct {
	consulKV *api.KV
}

type ConsulLoaderConfig struct {
	ConsulAddr string
	User       string
	Password   string
}

// NewConsulConfigLoader creates a new ConsulConfigLoader
func NewConsulConfigLoader(config ConsulLoaderConfig) (*ConsulConfigLoader, error) {
	consulClientCfg := &api.Config{
		Address: config.ConsulAddr,
	}
	if config.User != "" && config.Password != "" {
		consulClientCfg.HttpAuth = &api.HttpBasicAuth{
			Username: config.User,
			Password: config.Password,
		}
	}

	consulClient, err := api.NewClient(consulClientCfg)
	if err != nil {
		return nil, fmt.Errorf("failed to create consul client: %w", err)
	}
	return &ConsulConfigLoader{
		consulKV: consulClient.KV(),
	}, nil
}

// LoadConfig loads config from Consul
func (c *ConsulConfigLoader) LoadConfig(ctx context.Context, key string) (map[string]interface{}, error) {
	contextOpt := &api.QueryOptions{}
	contextOpt = contextOpt.WithContext(ctx)

	pair, _, err := c.consulKV.Get(key, contextOpt)
	if err != nil {
		return nil, err
	}

	if pair == nil {
		return nil, fmt.Errorf("key %s not found", key)
	}

	ext := filepath.Ext(key)
	if ext == "" {
		return map[string]interface{}{key: string(pair.Value)}, nil
	}

	v := viper.New()

	switch ext {
	case ".json":
		v.SetConfigType("json")
	case ".yaml", ".yml":
		v.SetConfigType("yaml")
	case ".toml":
		v.SetConfigType("toml")
	default:
		return nil, fmt.Errorf("unsupported config format: %s", ext)
	}

	if err := v.ReadConfig(bytes.NewReader(pair.Value)); err != nil {
		return nil, fmt.Errorf("failed to parse %s: %w", ext, err)
	}

	return v.AllSettings(), nil
}

// LoadConfigToGlobal loads config from Consul and set it to global viper
func (c *ConsulConfigLoader) LoadConfigToGlobal(ctx context.Context, key string) error {
	kvs, err := c.LoadConfig(ctx, key)
	if err != nil {
		return err
	}

	for k, v := range kvs {
		viper.Set(k, v)
	}
	return nil
}

// LoadConfigsToGlobal loads configs from Consul and set it to global viper
func (c *ConsulConfigLoader) LoadConfigsToGlobal(ctx context.Context, keys ...string) error {
	var g errgroup.Group
	for _, key := range keys {
		key := key
		g.Go(func() error {
			return c.LoadConfigToGlobal(ctx, key)
		})
	}
	return g.Wait()
}
