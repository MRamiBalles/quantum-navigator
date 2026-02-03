// CSV Export Utility for Benchmark Results

export interface ExportableData {
  [key: string]: string | number | boolean;
}

/**
 * Convert array of objects to CSV string
 */
export function arrayToCsv(data: ExportableData[], headers?: string[]): string {
  if (data.length === 0) return "";
  
  const keys = headers || Object.keys(data[0]);
  const csvRows: string[] = [];
  
  // Header row
  csvRows.push(keys.join(","));
  
  // Data rows
  for (const row of data) {
    const values = keys.map(key => {
      const val = row[key];
      // Escape quotes and wrap in quotes if contains comma
      if (typeof val === "string" && (val.includes(",") || val.includes('"'))) {
        return `"${val.replace(/"/g, '""')}"`;
      }
      return String(val ?? "");
    });
    csvRows.push(values.join(","));
  }
  
  return csvRows.join("\n");
}

/**
 * Download CSV file
 */
export function downloadCsv(csvContent: string, filename: string): void {
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename.endsWith(".csv") ? filename : `${filename}.csv`;
  link.style.display = "none";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Export benchmark data to CSV
 */
export async function exportBenchmarkToCsv(
  benchmarkType: string,
  customData?: ExportableData[]
): Promise<void> {
  const timestamp = new Date().toISOString().split("T")[0];
  const filename = `benchmark_${benchmarkType}_${timestamp}.csv`;
  
  let data: ExportableData[] = [];
  
  if (customData) {
    data = customData;
  } else {
    // Fetch from JSON files
    try {
      const response = await fetch(`/data/benchmark_${benchmarkType}.json`);
      if (response.ok) {
        data = await response.json();
      }
    } catch (error) {
      console.error(`Failed to fetch benchmark data for ${benchmarkType}:`, error);
      throw new Error(`Could not load ${benchmarkType} data`);
    }
  }
  
  if (data.length === 0) {
    throw new Error("No data to export");
  }
  
  const csv = arrayToCsv(data);
  downloadCsv(csv, filename);
}

/**
 * Export all benchmarks to a combined CSV
 */
export async function exportAllBenchmarks(): Promise<void> {
  const benchmarkTypes = [
    "velocity_fidelity",
    "ancilla_vs_swap", 
    "cooling_strategies",
    "zoned_cycles",
    "sustainable_depth"
  ];
  
  const timestamp = new Date().toISOString().split("T")[0];
  const allData: { benchmark: string; data: string }[] = [];
  
  for (const type of benchmarkTypes) {
    try {
      const response = await fetch(`/data/benchmark_${type}.json`);
      if (response.ok) {
        const data = await response.json();
        allData.push({
          benchmark: type,
          data: JSON.stringify(data)
        });
      }
    } catch (error) {
      console.warn(`Skipping ${type}: not available`);
    }
  }
  
  // Create combined export
  const combined = {
    exportedAt: new Date().toISOString(),
    version: "4.0",
    benchmarks: allData.reduce((acc, item) => {
      acc[item.benchmark] = JSON.parse(item.data);
      return acc;
    }, {} as Record<string, unknown>)
  };
  
  const blob = new Blob([JSON.stringify(combined, null, 2)], { 
    type: "application/json" 
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `quantum_navigator_benchmarks_${timestamp}.json`;
  link.click();
  URL.revokeObjectURL(url);
}
