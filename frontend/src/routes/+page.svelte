<script lang="ts">
  let file = $state<File | null>(null);
  let loading = $state(false);
  let invoiceData = $state<any>(null);

  function handleFileChange(event: Event) {
    const target = event.target as HTMLInputElement;
    if (target.files && target.files.length > 0) {
      file = target.files[0];
    }
  }

  async function uploadInvoice(event: Event) {
    event.preventDefault();
    if (!file) return;

    loading = true;
    const formData = new FormData();
    formData.append("file", file);

    try {
      // Notice the relative URL. Vite intercepts this and sends it to port 8000.
      const response = await fetch("/api/extract", {
        method: "POST",
        body: formData
      });
      
      if (!response.ok) throw new Error("Server returned an error");
      
      const result = await response.json();
      invoiceData = result.data;
    } catch (error) {
      console.error("Upload failed:", error);
      alert("Failed to extract data. Is the FastAPI server running?");
    } finally {
      loading = false;
    }
  }
</script>

<main class="min-h-screen bg-gray-50 p-8">
  <div class="max-w-2xl mx-auto space-y-8">
    <h1 class="text-3xl font-bold text-gray-900">Multimodal Invoice Agent</h1>
    
    <form onsubmit={uploadInvoice} class="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <div class="space-y-4">
        <label class="block text-sm font-medium text-gray-700">Upload PDF Invoice</label>
        <input 
          type="file" 
          accept=".pdf"
          onchange={handleFileChange}
          class="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700"
        />
        <button 
          type="submit" 
          disabled={!file || loading}
          class="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Agent is parsing...' : 'Extract Data'}
        </button>
      </div>
    </form>

    {#if invoiceData}
      <div class="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <h2 class="text-xl font-semibold mb-4">Structured Output</h2>
        <pre class="bg-gray-100 p-4 rounded-md overflow-x-auto text-sm">{JSON.stringify(invoiceData, null, 2)}</pre>
      </div>
    {/if}
  </div>
</main>