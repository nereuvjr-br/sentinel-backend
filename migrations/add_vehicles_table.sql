-- Migration: Add sentinel_vehicles table
-- Date: 2025-12-26
-- Description: Adiciona tabela para rastreamento de lifecycle de veículos (spawn, destroy, ownership)

CREATE TABLE IF NOT EXISTS sentinel_vehicles (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    
    -- Vehicle Identity
    vehicle_id VARCHAR(255) NOT NULL,
    vehicle_class VARCHAR(255) NOT NULL,
    
    -- Event
    event_type VARCHAR(100) NOT NULL,
    
    -- Context
    owner_id VARCHAR(255),
    owner_name VARCHAR(255),
    
    -- Location
    location JSONB,
    
    -- System
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes para performance
CREATE INDEX idx_vehicles_timestamp ON sentinel_vehicles(timestamp);
CREATE INDEX idx_vehicles_vehicle_id ON sentinel_vehicles(vehicle_id);
CREATE INDEX idx_vehicles_vehicle_class ON sentinel_vehicles(vehicle_class);
CREATE INDEX idx_vehicles_owner_id ON sentinel_vehicles(owner_id);
CREATE INDEX idx_vehicles_event_type ON sentinel_vehicles(event_type);

-- Comentários
COMMENT ON TABLE sentinel_vehicles IS 'Registra eventos de lifecycle de veículos (spawn, destroy, ownership changes)';
COMMENT ON COLUMN sentinel_vehicles.vehicle_id IS 'ID único do veículo no banco de dados do jogo';
COMMENT ON COLUMN sentinel_vehicles.vehicle_class IS 'Classe do veículo (ex: BPC_Laika, BPC_Wolfswagen)';
COMMENT ON COLUMN sentinel_vehicles.event_type IS 'Tipo de evento (Spawned, Destroyed, OwnershipChanged)';
COMMENT ON COLUMN sentinel_vehicles.owner_id IS 'SteamID do proprietário (se houver)';
COMMENT ON COLUMN sentinel_vehicles.location IS 'Coordenadas {x, y, z} onde o evento ocorreu';
