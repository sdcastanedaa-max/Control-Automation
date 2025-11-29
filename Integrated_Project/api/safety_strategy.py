from typing import List, Dict, Optional
import time
import logging

logger = logging.getLogger(__name__)

class SafetyStrategy:
    def __init__(self, protocol_data: Dict):
        self.conditions: List[Dict] = []
        for cond in protocol_data['conditions']:
            self.conditions.append({
                'sensor': cond['sensor_type'],
                'threshold': cond['threshold'],
                'duration_ms': cond['duration_ms'],
                'triggered_at': None,
                'violation_count': 0
            })
        self.max_runtime_ms = protocol_data.get('max_total_runtime_ms', 1800000)
        self.start_time = time.time() * 1000
        self.relay_state = True
    
    def check_violations(self, temp: float, current: float) -> bool:
        """Returns True if safety violation → shutdown relay"""
        now_ms = time.time() * 1000
        
        for cond in self.conditions:
            value = temp if cond['sensor'] == 'temperature' else current
            elapsed_ms = (now_ms - cond['triggered_at']) if cond['triggered_at'] is not None else 0
            
            if value > cond['threshold']:
                if cond['triggered_at'] is None:
                    cond['triggered_at'] = now_ms
                    print(f"  ⚠️  {cond['sensor'].upper()} THRESHOLD EXCEEDED: {value:.1f} > {cond['threshold']} (timer started)")
                else:
                    time_remaining = cond['duration_ms'] - elapsed_ms
                    if time_remaining > 0:
                        print(f"  ⏱️  {cond['sensor'].upper()} still high: {value:.1f} > {cond['threshold']} ({time_remaining/1000:.1f}s remaining)")
                    
                    if elapsed_ms >= cond['duration_ms']:
                        cond['violation_count'] += 1
                        print(f"  🚨 VIOLATION CONFIRMED: {cond['sensor']} exceeded for {cond['duration_ms']/1000:.0f}s")
                        logger.warning(f"🚨 VIOLATION: {cond['sensor']} {value:.1f} > {cond['threshold']} for {cond['duration_ms']/1000}s")
                        return True
            else:
                if cond['triggered_at'] is not None:
                    print(f"  ✓ {cond['sensor'].upper()} recovered: {value:.1f} < {cond['threshold']} (timer reset)")
                cond['triggered_at'] = None
        
        runtime_ms = now_ms - self.start_time
        if runtime_ms > self.max_runtime_ms:
            print(f"  ⏰ Max runtime exceeded: {runtime_ms/1000:.0f}s > {self.max_runtime_ms/1000:.0f}s")
            logger.warning("⏰ Max runtime exceeded")
            return True
        
        return False
    
    def get_status(self) -> Dict:
        """Debug status report"""
        return {
            'relay_state': self.relay_state,
            'runtime_ms': time.time() * 1000 - self.start_time,
            'conditions': self.conditions
        }
