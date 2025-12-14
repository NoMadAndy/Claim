"""
Tests for energy monitoring functionality.

Tests cover:
- Energy metric creation and retrieval
- Energy statistics calculation
- Energy settings management
- Optimization suggestions
"""

import pytest
from datetime import datetime, timedelta

from app.models import EnergyMetric, EnergySettings, EnergyConsumptionType, get_cet_now
from app.services.energy_service import EnergyService
from app.schemas import EnergyMetricCreate, EnergySettingsUpdate, BatteryStatusResponse


class TestEnergyMetrics:
    """Tests for energy metrics recording and retrieval"""

    def test_create_energy_metric(self, test_db, test_user):
        """Test creating a new energy metric"""
        metric_data = EnergyMetricCreate(
            consumption_type=EnergyConsumptionType.GPS,
            battery_level=75.0,
            is_charging=False,
            activity_duration_seconds=60.0,
            gps_updates_count=10,
            estimated_battery_drain=0.5
        )

        metric = EnergyService.create_energy_metric(
            db=test_db,
            user_id=test_user.id,
            metric_data=metric_data
        )

        assert metric.id is not None
        assert metric.user_id == test_user.id
        assert metric.consumption_type == EnergyConsumptionType.GPS
        assert metric.battery_level == 75.0
        assert metric.is_charging is False
        assert metric.gps_updates_count == 10

    def test_get_energy_metrics(self, test_db, test_user):
        """Test retrieving energy metrics"""
        # Create multiple metrics
        for i in range(5):
            metric_data = EnergyMetricCreate(
                consumption_type=EnergyConsumptionType.GPS,
                battery_level=80.0 - i,
                is_charging=False
            )
            EnergyService.create_energy_metric(
                db=test_db,
                user_id=test_user.id,
                metric_data=metric_data
            )

        # Retrieve metrics
        metrics = EnergyService.get_energy_metrics(
            db=test_db,
            user_id=test_user.id,
            hours=24
        )

        assert len(metrics) == 5
        assert all(m.user_id == test_user.id for m in metrics)

    def test_filter_metrics_by_type(self, test_db, test_user):
        """Test filtering metrics by consumption type"""
        # Create metrics of different types
        gps_metric = EnergyMetricCreate(
            consumption_type=EnergyConsumptionType.GPS,
            battery_level=80.0
        )
        network_metric = EnergyMetricCreate(
            consumption_type=EnergyConsumptionType.NETWORK,
            battery_level=79.0
        )

        EnergyService.create_energy_metric(test_db, test_user.id, gps_metric)
        EnergyService.create_energy_metric(test_db, test_user.id, network_metric)

        # Filter by GPS
        gps_metrics = EnergyService.get_energy_metrics(
            db=test_db,
            user_id=test_user.id,
            hours=24,
            consumption_type=EnergyConsumptionType.GPS
        )

        assert len(gps_metrics) == 1
        assert gps_metrics[0].consumption_type == EnergyConsumptionType.GPS


class TestEnergyStats:
    """Tests for energy statistics and analysis"""

    def test_get_energy_stats(self, test_db, test_user):
        """Test getting comprehensive energy statistics"""
        # Create some test metrics
        for i in range(5):
            metric_data = EnergyMetricCreate(
                consumption_type=EnergyConsumptionType.GPS,
                battery_level=90.0 - i * 2,
                is_charging=False,
                estimated_battery_drain=0.5
            )
            EnergyService.create_energy_metric(
                db=test_db,
                user_id=test_user.id,
                metric_data=metric_data
            )

        # Get stats
        stats = EnergyService.get_energy_stats(
            db=test_db,
            user_id=test_user.id,
            current_battery=80.0,
            is_charging=False
        )

        assert stats.current_battery_level == 80.0
        assert stats.is_charging is False
        assert isinstance(stats.top_consumers, list)
        assert isinstance(stats.optimization_suggestions, list)
        assert stats.energy_saving_enabled is False

    def test_top_consumers_calculation(self, test_db, test_user):
        """Test identification of top energy consumers"""
        # Create metrics with different consumption types
        types_and_drains = [
            (EnergyConsumptionType.GPS, 2.0),
            (EnergyConsumptionType.GPS, 2.0),
            (EnergyConsumptionType.NETWORK, 1.0),
            (EnergyConsumptionType.TRACKING, 3.0),
        ]

        for consumption_type, drain in types_and_drains:
            metric_data = EnergyMetricCreate(
                consumption_type=consumption_type,
                battery_level=80.0,
                estimated_battery_drain=drain
            )
            EnergyService.create_energy_metric(
                db=test_db,
                user_id=test_user.id,
                metric_data=metric_data
            )

        metrics = EnergyService.get_energy_metrics(test_db, test_user.id, hours=24)
        top_consumers = EnergyService._get_top_consumers(metrics)

        assert len(top_consumers) > 0
        # Tracking should be top (3.0), then GPS (4.0 total), then Network (1.0)
        assert top_consumers[0]['type'] == 'gps'  # GPS has 4.0 total

    def test_optimization_suggestions_low_battery(self, test_db, test_user):
        """Test that suggestions are provided when battery is low"""
        stats = EnergyService.get_energy_stats(
            db=test_db,
            user_id=test_user.id,
            current_battery=15.0,  # Low battery
            is_charging=False
        )

        assert len(stats.optimization_suggestions) > 0
        # Should suggest enabling energy saving mode
        suggestions_text = ' '.join(stats.optimization_suggestions)
        assert 'battery' in suggestions_text.lower() or 'energy' in suggestions_text.lower()

    def test_optimization_suggestions_high_consumer(self, test_db, test_user):
        """Test suggestions for high energy consumers"""
        # Create many GPS metrics to make it a high consumer
        for i in range(10):
            metric_data = EnergyMetricCreate(
                consumption_type=EnergyConsumptionType.GPS,
                battery_level=80.0,
                estimated_battery_drain=5.0  # High drain
            )
            EnergyService.create_energy_metric(
                db=test_db,
                user_id=test_user.id,
                metric_data=metric_data
            )

        stats = EnergyService.get_energy_stats(
            db=test_db,
            user_id=test_user.id,
            current_battery=80.0,
            is_charging=False
        )

        suggestions_text = ' '.join(stats.optimization_suggestions)
        # Should mention GPS since it's the top consumer
        assert 'gps' in suggestions_text.lower() or 'location' in suggestions_text.lower()


class TestEnergySettings:
    """Tests for energy settings management"""

    def test_get_or_create_settings(self, test_db, test_user):
        """Test getting or creating default energy settings"""
        settings = EnergyService.get_or_create_settings(test_db, test_user.id)

        assert settings.user_id == test_user.id
        assert settings.energy_saving_enabled is False
        assert settings.auto_enable_at_battery == 20.0
        assert settings.gps_update_interval_normal == 1000
        assert settings.gps_update_interval_saving == 5000

    def test_update_settings(self, test_db, test_user):
        """Test updating energy settings"""
        # Get or create settings
        settings = EnergyService.get_or_create_settings(test_db, test_user.id)

        # Update settings
        update_data = EnergySettingsUpdate(
            energy_saving_enabled=True,
            gps_update_interval_normal=2000
        )

        updated_settings = EnergyService.update_settings(
            db=test_db,
            user_id=test_user.id,
            settings_update=update_data
        )

        assert updated_settings.energy_saving_enabled is True
        assert updated_settings.gps_update_interval_normal == 2000
        # Other fields should remain unchanged
        assert updated_settings.gps_update_interval_saving == 5000

    def test_settings_persist_across_calls(self, test_db, test_user):
        """Test that settings are persisted in database"""
        # Create and update settings
        update_data = EnergySettingsUpdate(energy_saving_enabled=True)
        EnergyService.update_settings(test_db, test_user.id, update_data)

        # Get settings again
        settings = EnergyService.get_or_create_settings(test_db, test_user.id)

        assert settings.energy_saving_enabled is True


class TestEnergyAPI:
    """Tests for energy monitoring API endpoints"""

    def test_create_metric_endpoint(self, client, auth_headers):
        """Test POST /api/energy/metrics endpoint"""
        metric_data = {
            "consumption_type": "gps",
            "battery_level": 75.0,
            "is_charging": False,
            "gps_updates_count": 10
        }

        response = client.post(
            "/api/energy/metrics",
            json=metric_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["consumption_type"] == "gps"
        assert data["battery_level"] == 75.0
        assert "id" in data

    def test_get_metrics_endpoint(self, client, auth_headers):
        """Test GET /api/energy/metrics endpoint"""
        # Create a metric first
        metric_data = {
            "consumption_type": "network",
            "battery_level": 80.0
        }
        client.post("/api/energy/metrics", json=metric_data, headers=auth_headers)

        # Get metrics
        response = client.get("/api/energy/metrics", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_get_stats_endpoint(self, client, auth_headers):
        """Test POST /api/energy/stats endpoint"""
        battery_status = {
            "level": 75.0,
            "charging": False
        }

        response = client.post(
            "/api/energy/stats",
            json=battery_status,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "current_battery_level" in data
        assert "optimization_suggestions" in data
        assert "top_consumers" in data

    def test_get_settings_endpoint(self, client, auth_headers):
        """Test GET /api/energy/settings endpoint"""
        response = client.get("/api/energy/settings", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "energy_saving_enabled" in data
        assert "gps_update_interval_normal" in data

    def test_update_settings_endpoint(self, client, auth_headers):
        """Test PATCH /api/energy/settings endpoint"""
        settings_update = {
            "energy_saving_enabled": True,
            "gps_update_interval_normal": 3000
        }

        response = client.patch(
            "/api/energy/settings",
            json=settings_update,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["energy_saving_enabled"] is True
        assert data["gps_update_interval_normal"] == 3000

    def test_unauthorized_access(self, client):
        """Test that endpoints require authentication"""
        response = client.get("/api/energy/metrics")
        assert response.status_code == 401

    def test_filter_metrics_by_hours(self, client, auth_headers):
        """Test filtering metrics by time period"""
        response = client.get(
            "/api/energy/metrics?hours=12",
            headers=auth_headers
        )

        assert response.status_code == 200

    def test_filter_metrics_by_type(self, client, auth_headers):
        """Test filtering metrics by consumption type"""
        response = client.get(
            "/api/energy/metrics?consumption_type=gps",
            headers=auth_headers
        )

        assert response.status_code == 200


class TestEnergyCleanup:
    """Tests for energy metrics cleanup"""

    def test_cleanup_old_metrics(self, test_db, test_user):
        """Test cleanup of old energy metrics"""
        # Create an old metric
        old_metric = EnergyMetric(
            user_id=test_user.id,
            consumption_type=EnergyConsumptionType.GPS,
            battery_level=80.0,
            timestamp=get_cet_now() - timedelta(days=40)  # 40 days old
        )
        test_db.add(old_metric)
        test_db.commit()

        # Create a recent metric
        recent_metric = EnergyMetricCreate(
            consumption_type=EnergyConsumptionType.GPS,
            battery_level=75.0
        )
        EnergyService.create_energy_metric(test_db, test_user.id, recent_metric)

        # Run cleanup (keep last 30 days)
        deleted_count = EnergyService.cleanup_old_metrics(test_db, days=30)

        assert deleted_count == 1

        # Verify recent metric still exists
        metrics = EnergyService.get_energy_metrics(test_db, test_user.id, hours=24)
        assert len(metrics) == 1
