'use client';

import { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { MeshDistortMaterial, Sphere, OrbitControls } from '@react-three/drei';
import * as THREE from 'three';

function AnimatedBlob({ isActive }: { isActive: boolean }) {
  const meshRef = useRef<THREE.Mesh>(null);
  const materialRef = useRef<any>(null);

  useFrame((state) => {
    if (!meshRef.current) return;

    // Gentle rotation only when active
    if (isActive) {
      meshRef.current.rotation.y = state.clock.elapsedTime * 0.1;
    }
  });

  return (
    <Sphere ref={meshRef} args={[1, 128, 128]} scale={2.5} position={[3, 0, 0]}>
      <MeshDistortMaterial
        ref={materialRef}
        color="#1a1a1a"
        attach="material"
        distort={isActive ? 0.4 : 0.3}
        speed={isActive ? 2 : 0}
        roughness={0.2}
        metalness={0.6}
      />
    </Sphere>
  );
}

function Particles() {
  const particlesRef = useRef<THREE.Points>(null);

  const particles = useMemo(() => {
    const temp = [];
    for (let i = 0; i < 1000; i++) {
      const x = (Math.random() - 0.5) * 10;
      const y = (Math.random() - 0.5) * 10;
      const z = (Math.random() - 0.5) * 10;
      temp.push(x, y, z);
    }
    return new Float32Array(temp);
  }, []);

  // Particles remain static
  useFrame(() => {
    // No rotation for static view
  });

  return (
    <points ref={particlesRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={particles.length / 3}
          array={particles}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.02}
        color="#cccccc"
        transparent
        opacity={0.6}
        sizeAttenuation
      />
    </points>
  );
}

export default function AIVoiceAnimation({ isActive }: { isActive: boolean }) {
  return (
    <div className="w-full h-full">
      <Canvas
        camera={{ position: [0, 0, 5], fov: 75 }}
        style={{ background: 'linear-gradient(to bottom right, #f5f5f5, #e5e5e5)' }}
      >
        {/* Lighting */}
        <ambientLight intensity={0.5} />
        <directionalLight position={[10, 10, 5]} intensity={1} />
        <directionalLight position={[-10, -10, -5]} intensity={0.5} />
        <pointLight position={[0, 0, 0]} intensity={1} color="#ffffff" />

        {/* Animated Blob */}
        <AnimatedBlob isActive={isActive} />

        {/* Particle Field */}
        <Particles />

        {/* Orbit controls disabled to keep view static */}
        <OrbitControls
          enableZoom={false}
          enablePan={false}
          enabled={false}
        />
      </Canvas>
    </div>
  );
}
