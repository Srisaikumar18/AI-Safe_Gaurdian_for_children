"""
Continuous Learning System for MelodyWings Child Safety Platform
=================================================================

This module implements an adaptive learning system that improves toxicity detection
accuracy over time by learning from previously analyzed content.

ARCHITECTURE:
============

1. DATA COLLECTION LAYER
   - Stores analyzed transcripts with labels (safe/unsafe)
   - Captures user feedback and corrections
   - Tracks model predictions vs actual outcomes

2. FEATURE EXTRACTION LAYER
   - TF-IDF vectorization for text features
   - Custom feature engineering for child safety patterns
   - Contextual embeddings for semantic understanding

3. MODEL TRAINING LAYER
   - Incremental learning with new data batches
   - Model versioning and rollback capability
   - A/B testing between model versions

4. FEEDBACK LOOP
   - Manual review interface for borderline cases
   - Auto-correction based on high-confidence predictions
   - Active learning for uncertain predictions

5. MONITORING & EVALUATION
   - Real-time accuracy tracking
   - Drift detection for emerging toxic patterns
   - Performance metrics dashboard
"""

import sqlite3
import json
import os
import pickle
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.model_selection import train_test_split
import threading


class ContinuousLearningSystem:
    """
    Manages continuous improvement of child safety detection models.
    
    Features:
    - Learns from every analyzed video/audio
    - Adapts to new toxic patterns over time
    - Maintains model version history
    - Provides performance analytics
    """
    
    def __init__(self, db_path: str = "melodywings.db", model_dir: str = "models"):
        self.db_path = db_path
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)
        
        # CRITICAL: Initialize database tables FIRST before any operations
        self._init_learning_db()
        
        # Model state
        self.current_version = self._load_model_version()
        self.vectorizer = None
        self.model = None
        
        # Load or initialize model
        self._load_model()
        
        # Training buffer (accumulates new samples)
        self.training_buffer = []
        self.buffer_lock = threading.Lock()
        
        print(f"🧠 Continuous Learning System initialized (Version: {self.current_version})")
    
    # ========================================================================
    # DATABASE SCHEMA & INITIALIZATION
    # ========================================================================
    
    def _init_learning_db(self):
        """Initialize tables for continuous learning data with enhanced schema."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # ENHANCED: Store all transcribed texts with safety labels
        c.execute('''
        CREATE TABLE IF NOT EXISTS training_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            transcript_text TEXT NOT NULL,
            word_count INTEGER,
            toxic_words_detected TEXT,  -- JSON array
            safety_label TEXT NOT NULL,           -- 'safe', 'toxic', 'unsafe'
            human_reviewed BOOLEAN DEFAULT FALSE,
            human_label TEXT,
            confidence_score FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            source_type TEXT NOT NULL,             -- 'video', 'audio', 'chat'
            model_version TEXT,
            was_corrected BOOLEAN DEFAULT FALSE,
            correction_label TEXT,
            features_json TEXT
        )
        ''')
        
        # NEW: Store known toxic words with weights
        c.execute('''
        CREATE TABLE IF NOT EXISTS toxic_words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT UNIQUE NOT NULL,
            severity TEXT NOT NULL,               -- 'low', 'medium', 'high', 'critical'
            occurrence_count INTEGER DEFAULT 1,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            context_examples TEXT,                -- JSON array of example sentences
            for_children BOOLEAN DEFAULT TRUE
        )
        ''')
        
        # NEW: Store safe words/phrases (whitelist)
        c.execute('''
        CREATE TABLE IF NOT EXISTS safe_words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT UNIQUE NOT NULL,
            category TEXT,                        -- 'educational', 'positive', 'neutral'
            occurrence_count INTEGER DEFAULT 1
        )
        ''')
        
        # ENHANCED: Model versions and performance
        c.execute('''
        CREATE TABLE IF NOT EXISTS model_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version TEXT UNIQUE NOT NULL,
            trained_on DATE NOT NULL,
            accuracy FLOAT,
            precision FLOAT,
            recall FLOAT,
            f1_score FLOAT,
            is_active BOOLEAN DEFAULT FALSE,
            training_samples_count INTEGER,
            model_path TEXT,
            vectorizer_path TEXT,
            notes TEXT
        )
        ''')
        
        # Keep feedback table for user corrections
        c.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sample_id INTEGER NOT NULL,
            feedback_type TEXT NOT NULL,  -- 'false_positive', 'false_negative', 'correct'
            comment TEXT,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (sample_id) REFERENCES training_data(id)
        )
        ''')
        
        # Keep performance metrics for tracking
        c.execute('''
        CREATE TABLE IF NOT EXISTS performance_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            metric_name TEXT NOT NULL,
            metric_value REAL NOT NULL,
            model_version TEXT NOT NULL,
            sample_count INTEGER
        )
        ''')
        
        # Create comprehensive indexes for performance
        c.execute('CREATE INDEX IF NOT EXISTS idx_safety_label ON training_data(safety_label)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON training_data(created_at)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_source_type ON training_data(source_type)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_human_reviewed ON training_data(human_reviewed)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_toxic_word ON toxic_words(word)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_safe_word ON safe_words(word)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_model_active ON model_versions(is_active)')
        
        conn.commit()
        conn.close()
        
        print("✅ Database schema initialized with enhanced tables")
    
    # ========================================================================
    # DATA COLLECTION LAYER
    # ========================================================================
    
    def collect_sample(self, text: str, prediction: str, confidence: float, 
                      source: str, session_id: str = None, toxic_words: List[str] = None,
                      actual_label: Optional[str] = None):
        """
        Collect a training sample from analyzed content with enhanced metadata.
        
        Args:
            text: The transcribed/text content
            prediction: Model's prediction ('safe', 'toxic', or 'unsafe')
            confidence: Model's confidence score
            source: Content source ('chat', 'video', 'audio')
            session_id: Unique session identifier
            toxic_words: List of detected toxic words
            actual_label: True label if available (from human review)
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Use prediction as label if no actual label provided
        safety_label = actual_label if actual_label else prediction
        
        # Calculate word count
        word_count = len(text.split())
        
        # Convert toxic words to JSON array
        toxic_words_json = json.dumps(toxic_words) if toxic_words else json.dumps([])
        
        # Extract features for future training
        features = self._extract_features(text)
        
        # Determine severity based on toxic word count
        if toxic_words and len(toxic_words) > 0:
            severity = 'critical' if len(toxic_words) > 5 else 'high' if len(toxic_words) > 2 else 'medium'
        else:
            severity = 'low'
        
        # Insert into training_data table
        c.execute('''
        INSERT INTO training_data 
        (session_id, transcript_text, word_count, toxic_words_detected, safety_label,
         confidence_score, source_type, model_version, features_json, was_corrected)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id,
            text[:10000],  # Limit length
            word_count,
            toxic_words_json,
            safety_label,
            confidence,
            source,
            self.current_version,
            json.dumps(features),
            False
        ))
        
        sample_id = c.lastrowid
        
        # Update toxic words tracking
        if toxic_words:
            for word in toxic_words:
                self._update_toxic_word(word, severity, text[:200])
        
        # Update safe words if applicable
        if safety_label == 'safe' or (toxic_words and len(toxic_words) == 0):
            self._update_safe_words(text)
        
        conn.commit()
        conn.close()
        
        # Add to training buffer for incremental learning
        with self.buffer_lock:
            self.training_buffer.append({
                'id': sample_id,
                'text': text,
                'label': safety_label,
                'confidence': confidence,
                'source': source,
                'toxic_words': toxic_words or []
            })
        
        # Trigger retraining if buffer is large enough
        if len(self.training_buffer) >= 50:  # Retrain every 50 samples
            threading.Thread(target=self._trigger_retraining).start()
        
        return sample_id
    
    def _update_toxic_word(self, word: str, severity: str, context_example: str):
        """Update toxic word occurrence tracking."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Get existing examples
        c.execute('SELECT context_examples FROM toxic_words WHERE word = ?', (word,))
        row = c.fetchone()
        
        examples = []
        if row and row[0]:
            examples = json.loads(row[0])
            # Keep only last 5 examples
            examples = examples[-4:]
        
        examples.append(context_example)
        
        # Upsert toxic word
        c.execute('''
        INSERT INTO toxic_words (word, severity, occurrence_count, last_seen, context_examples)
        VALUES (?, ?, 1, ?, ?)
        ON CONFLICT(word) DO UPDATE SET
            occurrence_count = occurrence_count + 1,
            last_seen = excluded.last_seen,
            context_examples = excluded.context_examples,
            severity = excluded.severity
        ''', (word.lower(), severity, 
              datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
              json.dumps(examples)))
        
        conn.commit()
        conn.close()
    
    def _update_safe_words(self, text: str):
        """Extract and track safe words from positive content."""
        # Simple extraction - common positive/educational words
        positive_indicators = ['good', 'great', 'excellent', 'well done', 'perfect', 
                              'learn', 'education', 'school', 'teacher', 'friend',
                              'help', 'share', 'care', 'kind', 'nice']
        
        words = text.lower().split()
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        for word in words:
            clean_word = ''.join(filter(str.isalpha, word))
            if clean_word in positive_indicators or len(clean_word) > 3:
                c.execute('''
                INSERT INTO safe_words (word, category, occurrence_count)
                VALUES (?, 'positive', 1)
                ON CONFLICT(word) DO UPDATE SET
                    occurrence_count = occurrence_count + 1
                ''', (clean_word,))
        
        conn.commit()
        conn.close()
    
    def add_feedback(self, sample_id: int, feedback_type: str, comment: str = ""):
        """
        Add user feedback for a prediction.
        
        Args:
            sample_id: ID of the training sample
            feedback_type: 'false_positive', 'false_negative', or 'correct'
            comment: Optional comment explaining the feedback
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
        INSERT INTO feedback (sample_id, feedback_type, comment, timestamp)
        VALUES (?, ?, ?, ?)
        ''', (sample_id, feedback_type, comment, 
              datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        # Update sample if it was corrected (use new table name training_data)
        if feedback_type in ['false_positive', 'false_negative']:
            correct_label = 'safe' if feedback_type == 'false_positive' else 'unsafe'
            c.execute('''
            UPDATE training_data 
            SET was_corrected = TRUE, correction_label = ?
            WHERE id = ?
            ''', (correct_label, sample_id))
        
        conn.commit()
        conn.close()
        
        print(f"💾 Feedback recorded: Sample #{sample_id} - {feedback_type}")
    
    # ========================================================================
    # FEATURE EXTRACTION LAYER
    # ========================================================================
    
    def _extract_features(self, text: str) -> Dict:
        """Extract custom features for child safety detection."""
        text_lower = text.lower()
        
        features = {
            'length': len(text),
            'word_count': len(text.split()),
            'question_marks': text.count('?'),
            'exclamation_marks': text.count('!'),
            'personal_pronouns': sum([
                text_lower.count('i '), text_lower.count('you '),
                text_lower.count('we '), text_lower.count('us ')
            ]),
            'urgency_words': sum([
                text_lower.count('now'), text_lower.count('quick'),
                text_lower.count('fast'), text_lower.count('immediately')
            ]),
            'secrecy_words': sum([
                text_lower.count('secret'), text_lower.count('quiet'),
                text_lower.count('hide'), text_lower.count("don't tell")
            ]),
            'meeting_words': sum([
                text_lower.count('meet'), text_lower.count('come'),
                text_lower.count('visit'), text_lower.count('alone')
            ])
        }
        
        return features
    
    # ========================================================================
    # MODEL MANAGEMENT
    # ========================================================================
    
    def _load_model_version(self) -> str:
        """Load current model version from database."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Use trained_on instead of created_at (matches new schema)
        c.execute('''
        SELECT version FROM model_versions 
        WHERE is_active = TRUE 
        ORDER BY trained_on DESC LIMIT 1
        ''')
        
        row = c.fetchone()
        conn.close()
        
        if row:
            return row[0]
        else:
            # Initialize first version
            initial_version = "v1.0.0"
            self._save_model_version(initial_version, 0, 
                                   {"accuracy": 0.0, "precision": 0.0, 
                                    "recall": 0.0, "f1_score": 0.0})
            return initial_version
    
    def _save_model_version(self, version: str, num_samples: int, metrics: Dict):
        """Save new model version with performance metrics."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Deactivate all versions
        c.execute('UPDATE model_versions SET is_active = FALSE')
        
        # Save new version (use trained_on to match new schema)
        c.execute('''
        INSERT INTO model_versions 
        (version, trained_on, training_samples_count, accuracy, precision, 
         recall, f1_score, is_active, model_path, vectorizer_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            version,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            num_samples,
            metrics.get('accuracy', 0.0),
            metrics.get('precision', 0.0),
            metrics.get('recall', 0.0),
            metrics.get('f1_score', 0.0),
            True,
            os.path.join(self.model_dir, f"model_{version}.pkl"),
            os.path.join(self.model_dir, f"vectorizer_{version}.pkl")
        ))
        
        conn.commit()
        conn.close()
    
    def _load_model(self):
        """Load current model from disk or initialize new one."""
        try:
            model_path = os.path.join(self.model_dir, f"model_{self.current_version}.pkl")
            vectorizer_path = os.path.join(self.model_dir, f"vectorizer_{self.current_version}.pkl")
            
            if os.path.exists(model_path) and os.path.exists(vectorizer_path):
                with open(vectorizer_path, 'rb') as f:
                    self.vectorizer = pickle.load(f)
                with open(model_path, 'rb') as f:
                    self.model = pickle.load(f)
                print(f"✅ Loaded model {self.current_version}")
            else:
                # Initialize new model
                self._initialize_model()
                
        except Exception as e:
            print(f"⚠️ Error loading model: {e}")
            self._initialize_model()
    
    def _initialize_model(self):
        """Initialize a new model with default parameters."""
        print("🆕 Initializing new model...")
        
        # TF-IDF Vectorizer optimized for child safety
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),  # Unigrams and bigrams
            min_df=2,
            max_df=0.95,
            stop_words='english'
        )
        
        # SGD Classifier for incremental learning
        self.model = SGDClassifier(
            loss='log_loss',  # Logistic regression
            penalty='l2',
            alpha=0.0001,
            class_weight='balanced',
            random_state=42,
            warm_start=True  # Enable incremental learning
        )
        
        self.current_version = "v1.0.0"
        self._save_model()
    
    def _save_model(self):
        """Save current model to disk."""
        model_path = os.path.join(self.model_dir, f"model_{self.current_version}.pkl")
        vectorizer_path = os.path.join(self.model_dir, f"vectorizer_{self.current_version}.pkl")
        
        with open(vectorizer_path, 'wb') as f:
            pickle.dump(self.vectorizer, f)
        with open(model_path, 'wb') as f:
            pickle.dump(self.model, f)
        
        print(f"💾 Model saved: {model_path}")
    
    # ========================================================================
    # TRAINING & RETRAINING
    # ========================================================================
    
    def _trigger_retraining(self):
        """Trigger model retraining with accumulated data."""
        print("\n🔄 Starting automatic retraining...")
        
        try:
            # Get all training data
            conn = sqlite3.connect(self.db_path)
            
            # Include corrected samples with their corrections
            query = '''
            SELECT text_content, 
                   COALESCE(correction_label, label) as final_label
            FROM training_samples
            WHERE was_corrected = TRUE OR model_version != ?
            ORDER BY created_at DESC
            LIMIT 10000
            '''
            
            import pandas as pd
            df = pd.read_sql_query(query, conn, params=(self.current_version,))
            conn.close()
            
            if len(df) < 100:
                print(f"ℹ️ Not enough samples for retraining ({len(df)}/100)")
                return
            
            print(f"📊 Training on {len(df)} samples...")
            
            # Prepare data
            X_text = df['text_content'].values
            y = df['final_label'].values
            
            # Vectorize
            X = self.vectorizer.fit_transform(X_text)
            
            # Train/test split
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Train model
            self.model.partial_fit(X_train, y_train, 
                                  classes=np.array(['safe', 'unsafe']))
            
            # Evaluate
            y_pred = self.model.predict(X_test)
            
            metrics = {
                'accuracy': accuracy_score(y_test, y_pred),
                'precision': precision_score(y_test, y_pred, average='weighted'),
                'recall': recall_score(y_test, y_pred, average='weighted'),
                'f1_score': f1_score(y_test, y_pred, average='weighted')
            }
            
            # Create new version
            old_version = self.current_version
            self.current_version = f"v{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Save new model
            self._save_model()
            self._save_model_version(self.current_version, len(df), metrics)
            
            print(f"\n✅ Retraining complete!")
            print(f"📈 Metrics:")
            print(f"   Accuracy:  {metrics['accuracy']:.4f}")
            print(f"   Precision: {metrics['precision']:.4f}")
            print(f"   Recall:    {metrics['recall']:.4f}")
            print(f"   F1 Score:  {metrics['f1_score']:.4f}")
            print(f"🆕 New version: {self.current_version}")
            
            # Clear buffer
            with self.buffer_lock:
                self.training_buffer.clear()
            
            # Log performance metric
            self._log_performance_metric('accuracy', metrics['accuracy'])
            
        except Exception as e:
            print(f"❌ Retraining error: {e}")
            import traceback
            traceback.print_exc()
    
    def manual_retrain(self, min_samples: int = 100):
        """
        Manually trigger model retraining.
        
        Args:
            min_samples: Minimum samples required
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Use new table name training_data
        c.execute('SELECT COUNT(*) FROM training_data')
        count = c.fetchone()[0]
        conn.close()
        
        if count < min_samples:
            return {
                'success': False,
                'message': f'Not enough samples: {count}/{min_samples}'
            }
        
        # Start retraining in background thread
        thread = threading.Thread(target=self._trigger_retraining)
        thread.start()
        
        return {
            'success': True,
            'message': f'Retraining started with {count} samples',
            'samples_count': count
        }
    
    # ========================================================================
    # PREDICTION & INFERENCE
    # ========================================================================
    
    def predict(self, text: str) -> Tuple[str, float]:
        """
        Predict whether text is safe or unsafe.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Tuple of (prediction, confidence)
        """
        if self.model is None or self.vectorizer is None:
            return 'safe', 0.5
        
        try:
            # Vectorize
            X = self.vectorizer.transform([text])
            
            # Predict
            prediction = self.model.predict(X)[0]
            probabilities = self.model.predict_proba(X)[0]
            
            # Get confidence for predicted class
            class_idx = list(self.model.classes_).index(prediction)
            confidence = float(probabilities[class_idx])
            
            return prediction, confidence
            
        except Exception as e:
            print(f"⚠️ Prediction error: {e}")
            return 'safe', 0.5
    
    # ========================================================================
    # ANALYTICS & MONITORING
    # ========================================================================
    
    def get_analytics(self) -> Dict:
        """Get comprehensive analytics about the learning system with enhanced metrics."""
        conn = sqlite3.connect(self.db_path)
        
        try:
            import pandas as pd
            
            # Total samples
            total_samples = pd.read_sql_query(
                'SELECT COUNT(*) as count FROM training_data', conn
            ).iloc[0]['count']
            
            # Samples by label
            label_dist = pd.read_sql_query(
                'SELECT safety_label as label, COUNT(*) as count FROM training_data GROUP BY safety_label',
                conn
            )
            
            # Samples by source
            source_dist = pd.read_sql_query(
                'SELECT source_type, COUNT(*) as count FROM training_data GROUP BY source_type',
                conn
            )
            
            # Human reviewed stats
            reviewed_count = pd.read_sql_query(
                'SELECT COUNT(*) as count FROM training_data WHERE human_reviewed = TRUE',
                conn
            ).iloc[0]['count']
            
            # Toxic words tracking
            toxic_words_count = pd.read_sql_query(
                'SELECT COUNT(DISTINCT word) as count FROM toxic_words',
                conn
            ).iloc[0]['count']
            
            # Top toxic words
            top_toxic = pd.read_sql_query(
                '''SELECT word, severity, occurrence_count 
                   FROM toxic_words 
                   ORDER BY occurrence_count DESC LIMIT 10''',
                conn
            )
            
            # Safe words tracking
            safe_words_count = pd.read_sql_query(
                'SELECT COUNT(DISTINCT word) as count FROM safe_words',
                conn
            ).iloc[0]['count']
            
            # Recent performance
            recent_perf = pd.read_sql_query(
                '''SELECT metric_name, metric_value, model_version, timestamp
                   FROM performance_metrics
                   ORDER BY timestamp DESC LIMIT 10''',
                conn
            )
            
            # Feedback statistics
            feedback_stats = pd.read_sql_query(
                '''SELECT feedback_type, COUNT(*) as count 
                   FROM feedback 
                   GROUP BY feedback_type''',
                conn
            )
            
            # Model version info
            model_info = pd.read_sql_query(
                '''SELECT version, trained_on, accuracy, precision, recall, f1_score, training_samples_count
                   FROM model_versions 
                   WHERE is_active = TRUE''',
                conn
            )
            
            conn.close()
            
            return {
                'total_samples': total_samples,
                'label_distribution': label_dist.to_dict('records') if notlabel_dist.empty else [],
                'source_distribution': source_dist.to_dict('records') if not source_dist.empty else [],
                'human_reviewed_count': reviewed_count,
                'toxic_words_tracked': toxic_words_count,
                'safe_words_tracked': safe_words_count,
                'top_toxic_words': top_toxic.to_dict('records') if not top_toxic.empty else [],
                'recent_performance': recent_perf.to_dict('records') if not recent_perf.empty else [],
                'feedback_statistics': feedback_stats.to_dict('records') if not feedback_stats.empty else [],
                'current_model_version': self.current_version,
                'buffer_size': len(self.training_buffer),
                'active_model_info': model_info.to_dict('records')[0] if not model_info.empty else None
            }
            
        except Exception as e:
            print(f"❌ Error getting analytics: {e}")
            return {
                'total_samples': 0,
                'error': str(e)
            }
    
    def _log_performance_metric(self, metric_name: str, metric_value: float):
        """Log a performance metric to track over time."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
        INSERT INTO performance_metrics 
        (timestamp, metric_name, metric_value, model_version, sample_count)
        VALUES (?, ?, ?, ?, ?)
        ''', (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            metric_name,
            metric_value,
            self.current_version,
            len(self.training_buffer)
        ))
        
        conn.commit()
        conn.close()
    
    def export_training_data(self, output_path: str = "training_export.json"):
        """Export all training data for external analysis."""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
        SELECT text_content, label, confidence, source, 
               model_version, was_corrected, correction_label,
               timestamp
        FROM training_samples
        ORDER BY created_at DESC
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Convert to JSON
        data = df.to_dict('records')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"📦 Exported {len(data)} samples to {output_path}")
        return len(data)


# ============================================================================
# INTEGRATION WITH EXISTING SYSTEM
# ============================================================================

def integrate_with_melodywings():
    """
    Integrate continuous learning with existing MelodyWings system.
    
    This function should be called from app.py to enable learning.
    """
    # Initialize learning system
    learning_system = ContinuousLearningSystem()
    
    print("🔗 Continuous Learning integration complete")
    print("   - Every analyzed video/audio will improve the model")
    print("   - Automatic retraining every 50 new samples")
    print("   - Model versioning with performance tracking")
    
    return learning_system


if __name__ == "__main__":
    # Test the system
    cls = ContinuousLearningSystem()
    
    # Simulate some training data
    test_samples = [
        ("Hello friend, how are you?", "safe", 0.95),
        ("You are stupid and I hate you", "unsafe", 0.98),
        ("Let's meet alone at my place", "unsafe", 0.87),
        ("Great job on your homework!", "safe", 0.92),
    ]
    
    for text, label, conf in test_samples:
        cls.collect_sample(text, label, conf, "test")
        pred, conf = cls.predict(text)
        print(f"Text: {text}")
        print(f"Prediction: {pred} ({conf:.2f})")
        print()
