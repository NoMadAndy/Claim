"""
Energy monitoring and optimization service.

This service provides functionality for:
- Recording energy consumption metrics
- Analyzing battery usage patterns
- Providing optimization suggestions
- Managing energy-saving settings
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

from app.models import (
    EnergyMetric, 
    EnergySettings, 
    EnergyConsumptionType, 
    User,
    get_cet_now
)
from app.schemas import (
    EnergyMetricCreate,
    EnergyMetricResponse,
    EnergySettingsUpdate,
    EnergySettingsResponse,
    EnergyStatsResponse
)

logger = logging.getLogger(__name__)


class EnergyService:
    """Service for energy monitoring and optimization"""

    @staticmethod
    def create_energy_metric(
        db: Session,
        user_id: int,
        metric_data: EnergyMetricCreate
    ) -> EnergyMetric:
        """
        Record a new energy consumption metric.
        
        Args:
            db: Database session
            user_id: User ID
            metric_data: Energy metric data
            
        Returns:
            Created energy metric
        """
        energy_metric = EnergyMetric(
            user_id=user_id,
            consumption_type=metric_data.consumption_type,
            battery_level=metric_data.battery_level,
            is_charging=metric_data.is_charging,
            activity_duration_seconds=metric_data.activity_duration_seconds,
            gps_updates_count=metric_data.gps_updates_count,
            network_requests_count=metric_data.network_requests_count,
            websocket_messages_count=metric_data.websocket_messages_count,
            estimated_battery_drain=metric_data.estimated_battery_drain,
            timestamp=get_cet_now()
        )
        
        db.add(energy_metric)
        db.commit()
        db.refresh(energy_metric)
        
        logger.info(f"Energy metric recorded for user {user_id}: {metric_data.consumption_type}")
        
        return energy_metric

    @staticmethod
    def get_energy_metrics(
        db: Session,
        user_id: int,
        hours: int = 24,
        consumption_type: Optional[EnergyConsumptionType] = None
    ) -> List[EnergyMetric]:
        """
        Get energy metrics for a user within a time period.
        
        Args:
            db: Database session
            user_id: User ID
            hours: Number of hours to look back
            consumption_type: Optional filter by consumption type
            
        Returns:
            List of energy metrics
        """
        cutoff_time = get_cet_now() - timedelta(hours=hours)
        
        query = db.query(EnergyMetric).filter(
            EnergyMetric.user_id == user_id,
            EnergyMetric.timestamp >= cutoff_time
        )
        
        if consumption_type:
            query = query.filter(EnergyMetric.consumption_type == consumption_type)
        
        return query.order_by(desc(EnergyMetric.timestamp)).all()

    @staticmethod
    def get_energy_stats(
        db: Session,
        user_id: int,
        current_battery: Optional[float] = None,
        is_charging: bool = False
    ) -> EnergyStatsResponse:
        """
        Get comprehensive energy statistics and optimization suggestions.
        
        Args:
            db: Database session
            user_id: User ID
            current_battery: Current battery level (0-100)
            is_charging: Whether device is currently charging
            
        Returns:
            Energy statistics response
        """
        # Get recent metrics (last 24 hours)
        recent_metrics = EnergyService.get_energy_metrics(db, user_id, hours=24)
        
        # Calculate average battery drain per hour
        avg_drain = EnergyService._calculate_average_drain(recent_metrics)
        
        # Estimate time remaining
        time_remaining = None
        if current_battery and not is_charging and avg_drain and avg_drain > 0:
            time_remaining = current_battery / avg_drain
        
        # Identify top energy consumers
        top_consumers = EnergyService._get_top_consumers(recent_metrics)
        
        # Generate optimization suggestions
        suggestions = EnergyService._generate_suggestions(
            db, user_id, top_consumers, current_battery, is_charging
        )
        
        # Get current energy settings
        settings = EnergyService.get_or_create_settings(db, user_id)
        
        return EnergyStatsResponse(
            current_battery_level=current_battery,
            is_charging=is_charging,
            estimated_time_remaining_hours=time_remaining,
            average_battery_drain_per_hour=avg_drain,
            top_consumers=top_consumers,
            optimization_suggestions=suggestions,
            energy_saving_enabled=settings.energy_saving_enabled
        )

    @staticmethod
    def _calculate_average_drain(metrics: List[EnergyMetric]) -> Optional[float]:
        """Calculate average battery drain per hour from metrics"""
        if not metrics:
            return None
        
        # Filter metrics with battery level data
        battery_metrics = [m for m in metrics if m.battery_level is not None and not m.is_charging]
        
        if len(battery_metrics) < 2:
            return None
        
        # Sort by timestamp
        battery_metrics.sort(key=lambda x: x.timestamp)
        
        # Calculate drain rate
        first_metric = battery_metrics[0]
        last_metric = battery_metrics[-1]
        
        time_diff_hours = (last_metric.timestamp - first_metric.timestamp).total_seconds() / 3600
        battery_diff = first_metric.battery_level - last_metric.battery_level
        
        if time_diff_hours > 0 and battery_diff > 0:
            return battery_diff / time_diff_hours
        
        return None

    @staticmethod
    def _get_top_consumers(metrics: List[EnergyMetric]) -> List[Dict]:
        """Identify top energy consumers from metrics"""
        if not metrics:
            return []
        
        # Group by consumption type and count
        consumer_stats = {}
        
        for metric in metrics:
            consumption_type = metric.consumption_type.value
            
            if consumption_type not in consumer_stats:
                consumer_stats[consumption_type] = {
                    'type': consumption_type,
                    'count': 0,
                    'total_drain': 0.0
                }
            
            consumer_stats[consumption_type]['count'] += 1
            if metric.estimated_battery_drain:
                consumer_stats[consumption_type]['total_drain'] += metric.estimated_battery_drain
        
        # Calculate percentages
        total_drain = sum(s['total_drain'] for s in consumer_stats.values())
        
        for stats in consumer_stats.values():
            if total_drain > 0:
                stats['percentage'] = (stats['total_drain'] / total_drain) * 100
            else:
                stats['percentage'] = 0
        
        # Sort by percentage
        top_consumers = sorted(
            consumer_stats.values(),
            key=lambda x: x['percentage'],
            reverse=True
        )[:5]
        
        return top_consumers

    @staticmethod
    def _generate_suggestions(
        db: Session,
        user_id: int,
        top_consumers: List[Dict],
        current_battery: Optional[float],
        is_charging: bool
    ) -> List[str]:
        """Generate optimization suggestions based on usage patterns"""
        suggestions = []
        
        # Check if battery is low
        if current_battery and current_battery < 20 and not is_charging:
            suggestions.append("🔋 Battery is low! Consider enabling energy saving mode.")
        
        # Analyze top consumers and provide targeted suggestions
        for consumer in top_consumers[:3]:  # Top 3 consumers
            consumer_type = consumer['type']
            percentage = consumer['percentage']
            
            if percentage > 30:  # If consuming more than 30%
                if consumer_type == 'gps':
                    suggestions.append(
                        "📍 GPS is consuming significant battery. "
                        "Consider reducing location update frequency."
                    )
                elif consumer_type == 'network':
                    suggestions.append(
                        "🌐 Network requests are high. "
                        "Enable batch processing to reduce battery drain."
                    )
                elif consumer_type == 'tracking':
                    suggestions.append(
                        "🚶 Tracking is consuming battery. "
                        "Reduce tracking accuracy or stop tracking when not needed."
                    )
                elif consumer_type == 'websocket':
                    suggestions.append(
                        "🔌 WebSocket updates are frequent. "
                        "Consider reducing update frequency."
                    )
        
        # General suggestions if no specific issues found
        if not suggestions:
            suggestions.append("✅ Battery usage looks good! Keep using the app normally.")
        
        # Always suggest energy saving mode if not enabled and battery is not charging
        settings = EnergyService.get_or_create_settings(db, user_id)
        if not settings.energy_saving_enabled and not is_charging:
            if current_battery and current_battery < 30:
                suggestions.append(
                    "💡 Enable energy saving mode to extend battery life."
                )
        
        return suggestions

    @staticmethod
    def get_or_create_settings(db: Session, user_id: int) -> EnergySettings:
        """
        Get or create energy settings for a user.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Energy settings
        """
        settings = db.query(EnergySettings).filter(
            EnergySettings.user_id == user_id
        ).first()
        
        if not settings:
            settings = EnergySettings(user_id=user_id)
            db.add(settings)
            db.commit()
            db.refresh(settings)
            logger.info(f"Created default energy settings for user {user_id}")
        
        return settings

    @staticmethod
    def update_settings(
        db: Session,
        user_id: int,
        settings_update: EnergySettingsUpdate
    ) -> EnergySettings:
        """
        Update energy settings for a user.
        
        Args:
            db: Database session
            user_id: User ID
            settings_update: Updated settings data
            
        Returns:
            Updated energy settings
        """
        settings = EnergyService.get_or_create_settings(db, user_id)
        
        # Update fields that are provided
        update_data = settings_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(settings, field, value)
        
        settings.updated_at = get_cet_now()
        
        db.commit()
        db.refresh(settings)
        
        logger.info(f"Updated energy settings for user {user_id}")
        
        return settings

    @staticmethod
    def cleanup_old_metrics(db: Session, days: int = 30) -> int:
        """
        Clean up old energy metrics to save database space.
        
        Args:
            db: Database session
            days: Number of days to keep
            
        Returns:
            Number of deleted records
        """
        cutoff_date = get_cet_now() - timedelta(days=days)
        
        deleted = db.query(EnergyMetric).filter(
            EnergyMetric.timestamp < cutoff_date
        ).delete()
        
        db.commit()
        
        logger.info(f"Cleaned up {deleted} old energy metrics older than {days} days")
        
        return deleted
