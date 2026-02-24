/**
 * Sample TypeScript file for testing chunking.
 */

export interface SampleInterface {
  name: string;
  value: number;
}

export class SampleClass implements SampleInterface {
  name: string;
  value: number;

  constructor(name: string, value: number) {
    this.name = name;
    this.value = value;
  }

  getInfo(): string {
    return `${this.name}: ${this.value}`;
  }
}

export function sampleFunction(x: number): number {
  return x * 2;
}

// Main execution
const obj = new SampleClass("test", 10);
console.log(obj.getInfo());
