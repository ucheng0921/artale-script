"""
圖像處理線程模組 - 負責後台圖像處理和檢測
"""
import threading
import queue
import time
from dataclasses import dataclass
from typing import Optional, Tuple, Any
import cv2


@dataclass
class ImageTask:
    """圖像處理任務"""
    task_id: str
    task_type: str  # 'detect_monster', 'find_medal', 'detect_sign', 'detect_rune', 'scan_direction'
    screenshot: Any
    params: dict
    timestamp: float


@dataclass
class ImageResult:
    """圖像處理結果"""
    task_id: str
    task_type: str
    success: bool
    result: Any
    timestamp: float
    processing_time: float


class ImageProcessor:
    """圖像處理器 - 在獨立線程中運行"""
    
    def __init__(self):
        self.task_queue = queue.Queue(maxsize=10)  # 限制隊列大小避免內存堆積
        self.result_queue = queue.Queue(maxsize=50)
        self.worker_thread = None
        self.running = False
        self.components = {}
        self.templates = {}
        
        # 性能統計
        self.processed_tasks = 0
        self.total_processing_time = 0
        
    def start(self, components, templates):
        """啟動圖像處理線程"""
        self.components = components
        self.templates = templates
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        print("🚀 圖像處理線程已啟動")
        
    def stop(self):
        """停止圖像處理線程"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=2.0)
        print("🛑 圖像處理線程已停止")
        
    def submit_task(self, task_type: str, screenshot, params: dict) -> str:
        """提交圖像處理任務"""
        task_id = f"{task_type}_{time.time():.6f}"
        task = ImageTask(
            task_id=task_id,
            task_type=task_type,
            screenshot=screenshot,
            params=params,
            timestamp=time.time()
        )
        
        try:
            # 非阻塞提交，如果隊列滿了就丟棄舊任務
            self.task_queue.put_nowait(task)
            return task_id
        except queue.Full:
            # 隊列滿了，清空一些舊任務
            try:
                while not self.task_queue.empty():
                    old_task = self.task_queue.get_nowait()
                self.task_queue.put_nowait(task)
                return task_id
            except queue.Empty:
                pass
            return None
    
    def get_result(self, timeout: float = 0.001) -> Optional[ImageResult]:
        """獲取處理結果"""
        try:
            return self.result_queue.get_nowait()
        except queue.Empty:
            return None
    
    def get_latest_result(self, task_type: str) -> Optional[ImageResult]:
        """獲取指定類型的最新結果"""
        latest_result = None
        latest_time = 0
        
        # 收集所有結果
        results = []
        try:
            while True:
                result = self.result_queue.get_nowait()
                results.append(result)
        except queue.Empty:
            pass
        
        # 找到最新的指定類型結果
        for result in results:
            if result.task_type == task_type and result.timestamp > latest_time:
                latest_result = result
                latest_time = result.timestamp
        
        # 把其他結果放回隊列
        for result in results:
            if result != latest_result:
                try:
                    self.result_queue.put_nowait(result)
                except queue.Full:
                    pass  # 隊列滿了就丟棄
                    
        return latest_result
    
    def _worker_loop(self):
        """工作線程主循環"""
        print("🔄 圖像處理工作線程開始運行")
        
        while self.running:
            try:
                # 獲取任務，最多等待0.1秒
                task = self.task_queue.get(timeout=0.1)
                
                # 處理任務
                start_time = time.time()
                result = self._process_task(task)
                processing_time = time.time() - start_time
                
                # 創建結果
                image_result = ImageResult(
                    task_id=task.task_id,
                    task_type=task.task_type,
                    success=result is not None,
                    result=result,
                    timestamp=time.time(),
                    processing_time=processing_time
                )
                
                # 提交結果
                try:
                    self.result_queue.put_nowait(image_result)
                except queue.Full:
                    # 結果隊列滿了，清理一些舊結果
                    try:
                        for _ in range(10):  # 清理10個舊結果
                            self.result_queue.get_nowait()
                        self.result_queue.put_nowait(image_result)
                    except queue.Empty:
                        pass
                
                # 更新統計
                self.processed_tasks += 1
                self.total_processing_time += processing_time
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"❌ 圖像處理錯誤: {e}")
                continue
    
    def _process_task(self, task: ImageTask):
        """處理具體的圖像任務"""
        try:
            if task.task_type == 'detect_monster':
                return self._detect_monster(task.screenshot, task.params)
            elif task.task_type == 'find_medal':
                return self._find_medal(task.screenshot, task.params)
            elif task.task_type == 'detect_sign':
                return self._detect_sign(task.screenshot, task.params)
            elif task.task_type == 'detect_rune':
                return self._detect_rune(task.screenshot, task.params)
            elif task.task_type == 'scan_direction':
                return self._scan_direction(task.screenshot, task.params)
            else:
                print(f"⚠️ 未知任務類型: {task.task_type}")
                return None
        except Exception as e:
            print(f"❌ 處理任務失敗 {task.task_type}: {e}")
            return None
    
    def _detect_monster(self, screenshot, params):
        """怪物檢測"""
        detector = self.components.get('monster_detector')
        if not detector:
            return None
            
        return detector.detect_monsters(
            screenshot, 
            params['player_x'], 
            params['player_y'],
            params['client_width'], 
            params['client_height'],
            params['movement'], 
            params['cliff_detection'],
            params['client_x'], 
            params['client_y']
        )
    
    def _find_medal(self, screenshot, params):
        """角色檢測"""
        from core.utils import simple_find_medal
        
        medal_template = self.templates.get('medal')
        if medal_template is None:
            return None
            
        threshold = params.get('threshold', 0.6)
        found, loc, val = simple_find_medal(screenshot, medal_template, threshold)
        
        if found:
            template_height, template_width = medal_template.shape[:2]
            player_x = loc[0] + template_width // 2
            player_y = loc[1] + template_height // 2 - params.get('y_offset', 50)
            return {
                'found': True,
                'location': loc,
                'match_value': val,
                'player_x': player_x,
                'player_y': player_y
            }
        return {'found': False, 'match_value': val}
    
    def _detect_sign(self, screenshot, params):
        """檢測sign_text"""
        from core.utils import detect_sign_text
        
        sign_template = self.templates.get('sign')
        if sign_template is None:
            return None
            
        threshold = params.get('threshold', 0.65)
        found, loc, val = detect_sign_text(screenshot, sign_template, threshold)
        
        return {
            'found': found,
            'location': loc,
            'match_value': val
        }
    
    def _detect_rune(self, screenshot, params):
        """檢測rune_text"""
        from core.utils import simple_find_medal
        
        rune_template = self.templates.get('rune')
        if rune_template is None:
            return None
            
        threshold = params.get('threshold', 0.6)
        found, loc, val = simple_find_medal(screenshot, rune_template, threshold)
        
        return {
            'found': found,
            'location': loc,
            'match_value': val
        }
    
    def _scan_direction(self, screenshot, params):
        """遠距離方向掃描"""
        detector = self.components.get('monster_detector')
        if not detector:
            return None
            
        direction, target_y = detector.scan_for_direction(
            screenshot,
            params['player_x'],
            params['player_y'],
            params['client_width'],
            params['client_height'],
            params['movement']
        )
        
        return {
            'direction': direction,
            'target_y': target_y
        }
    
    def get_stats(self):
        """獲取處理統計"""
        if self.processed_tasks == 0:
            return "圖像處理統計: 尚無數據"
        
        avg_time = self.total_processing_time / self.processed_tasks
        return f"圖像處理統計: 已處理 {self.processed_tasks} 個任務, 平均耗時 {avg_time*1000:.1f}ms"