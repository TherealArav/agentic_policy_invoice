<script lang="ts">
	let file = $state<File | null>(null);
	let loading = $state(false);
	let invoiceData = $state<any>(null);
	let needsReview = $state<boolean>(false);
	let routingMessage = $state<string>('');

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
		formData.append('file', file);

		try {
			// Notice the relative URL. Vite intercepts this and sends it to port 8000.
			const response = await fetch('/api/extract', {
				method: 'POST',
				body: formData
			});

			if (!response.ok) throw new Error('Server returned an error');

			const result = await response.json();
			invoiceData = result.data;
			needsReview = result.needs_review;
			routingMessage = result.routing_message;
		} catch (error) {
			console.error('Upload failed:', error);
			alert('Failed to extract data. Is the FastAPI server running?');
		} finally {
			loading = false;
		}
	}
</script>

<main class="min-h-screen bg-gray-50 p-8">
	<div class="mx-auto max-w-2xl space-y-8">
		<h1 class="text-3xl font-bold text-gray-900">Multimodal Invoice Agent</h1>

		<form onsubmit={uploadInvoice} class="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
			<div class="space-y-4">
				<label class="block text-sm font-medium text-gray-700">Upload PDF Invoice</label>
				<input
					type="file"
					accept=".pdf"
					onchange={handleFileChange}
					class="block w-full text-sm text-gray-500 file:mr-4 file:rounded-md file:border-0 file:bg-blue-50 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-blue-700"
				/>
				<button
					type="submit"
					disabled={!file || loading}
					class="w-full rounded-md bg-blue-600 px-4 py-2 text-white transition-colors hover:bg-blue-700 disabled:opacity-50"
				>
					{loading ? 'Agent is parsing...' : 'Extract Data'}
				</button>
			</div>
		</form>

		{#if invoiceData}
			<div class="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
				<h2 class="mb-4 text-xl font-semibold">Structured Output</h2>

				<!-- 3. Insert the dynamic Validation Banner -->
				<div
					class="mb-6 rounded-md border p-4 {needsReview
						? 'border-red-200 bg-red-50'
						: 'border-green-200 bg-green-50'}"
				>
					<div class="flex items-center space-x-3">
						<span
							class="h-3 w-3 flex-shrink-0 rounded-full {needsReview
								? 'bg-red-600'
								: 'bg-green-600'}"
						></span>
						<div>
							<h3 class="text-sm font-medium {needsReview ? 'text-red-800' : 'text-green-800'}">
								{needsReview ? 'Human Review Required' : 'Automated Verification Passed'}
							</h3>
							<p class="mt-1 text-sm {needsReview ? 'text-red-700' : 'text-green-700'}">
								{routingMessage}
							</p>
						</div>
					</div>
				</div>

				<pre class="overflow-x-auto rounded-md bg-gray-100 p-4 text-sm">{JSON.stringify(
						invoiceData,
						null,
						2
					)}</pre>
			</div>
		{/if}
	</div>
</main>
