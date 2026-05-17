import openapiTS from 'openapi-typescript';
import { writeFileSync } from 'fs';

async function generateTypes() {
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:9000';
  const OUTPUT_PATH = 'src/services/api/types/schema.ts';
  
  console.log('🔄 Generating TypeScript types from OpenAPI...');
  
  try {
    const ast = await openapiTS(`${API_URL}/openapi.json`);
    const output = `// ⚠️ AUTO-GENERATED — DO NOT EDIT\n// Source: ${API_URL}/openapi.json\n\n` + ast;
    
    writeFileSync(OUTPUT_PATH, output);
    console.log(`✅ Types generated: ${OUTPUT_PATH}`);
  } catch (error) {
    console.error('❌ Failed to generate types:', error);
    process.exit(1);
  }
}

generateTypes();
