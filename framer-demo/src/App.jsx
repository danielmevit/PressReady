import { motion } from "framer-motion";
import { useState } from "react";

function App() {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="app">
      <motion.h1
        initial={{ opacity: 0, y: -50 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
      >
        Framer Motion Demo
      </motion.h1>

      {/* Demo 1: Basic Animation */}
      <div className="demo-section">
        <h2>1. Hover & Tap Animation</h2>
        <div className="demo-area">
          <motion.div
            className="box"
            whileHover={{ scale: 1.2, rotate: 10 }}
            whileTap={{ scale: 0.9 }}
            transition={{ type: "spring", stiffness: 300 }}
          />
        </div>
        <p className="instructions">Hover over the box and click it!</p>
      </div>

      {/* Demo 2: Toggle Animation */}
      <div className="demo-section">
        <h2>2. Click to Expand</h2>
        <div className="demo-area">
          <motion.div
            className="card"
            onClick={() => setIsExpanded(!isExpanded)}
            animate={{
              scale: isExpanded ? 1.2 : 1,
              backgroundColor: isExpanded ? "#667eea" : "#f5576c",
            }}
            transition={{ duration: 0.3 }}
          >
            <h3>{isExpanded ? "Expanded!" : "Click Me"}</h3>
            <p>{isExpanded ? "Click to shrink" : "I will grow"}</p>
          </motion.div>
        </div>
      </div>

      {/* Demo 3: Staggered Animation */}
      <div className="demo-section">
        <h2>3. Staggered Children</h2>
        <div className="demo-area">
          <motion.div
            className="stagger-container"
            initial="hidden"
            animate="visible"
            variants={{
              hidden: { opacity: 0 },
              visible: {
                opacity: 1,
                transition: {
                  staggerChildren: 0.15,
                },
              },
            }}
          >
            {[0, 1, 2, 3, 4].map((i) => (
              <motion.div
                key={i}
                className="stagger-item"
                variants={{
                  hidden: { y: 50, opacity: 0 },
                  visible: { y: 0, opacity: 1 },
                }}
                whileHover={{ y: -10 }}
              />
            ))}
          </motion.div>
        </div>
        <p className="instructions">Watch them appear one by one, then hover!</p>
      </div>

      {/* Demo 4: Drag */}
      <div className="demo-section">
        <h2>4. Drag Me Around</h2>
        <div className="demo-area" style={{ minHeight: "200px" }}>
          <motion.div
            className="drag-box"
            drag
            dragConstraints={{ left: -100, right: 100, top: -50, bottom: 50 }}
            whileDrag={{ scale: 1.1 }}
          >
            Drag!
          </motion.div>
        </div>
      </div>

      {/* Demo 5: Keyframes */}
      <div className="demo-section">
        <h2>5. Keyframe Animation (Looping)</h2>
        <div className="demo-area">
          <motion.div
            className="box"
            animate={{
              scale: [1, 1.2, 1.2, 1, 1],
              rotate: [0, 0, 180, 180, 0],
              borderRadius: ["16px", "16px", "50%", "50%", "16px"],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              repeatDelay: 1,
            }}
          />
        </div>
        <p className="instructions">This loops forever with keyframes</p>
      </div>
    </div>
  );
}

export default App;
