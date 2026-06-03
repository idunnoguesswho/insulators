param(
    [Parameter(Mandatory = $true)]
    [string]$ImagePath
)

Add-Type -AssemblyName System.Runtime.WindowsRuntime

$null = [Windows.Globalization.Language, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]

function Await-WinRt($Operation, $ResultType) {
    $asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() |
        Where-Object {
            $_.Name -eq "AsTask" -and
            $_.GetParameters().Count -eq 1 -and
            $_.GetParameters()[0].ParameterType.Name -eq "IAsyncOperation``1"
        } |
        Select-Object -First 1).MakeGenericMethod($ResultType)
    $task = $asTask.Invoke($null, @($Operation))
    $task.Wait()
    $task.Result
}

$resolved = (Resolve-Path -LiteralPath $ImagePath).Path
$storageFile = Await-WinRt ([Windows.Storage.StorageFile]::GetFileFromPathAsync($resolved)) ([Windows.Storage.StorageFile])
$stream = Await-WinRt ($storageFile.OpenReadAsync()) ([Windows.Storage.Streams.IRandomAccessStreamWithContentType])
$decoder = Await-WinRt ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
$bitmap = Await-WinRt ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])

$language = [Windows.Globalization.Language]::new("en-US")
$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($language)
if ($null -eq $engine) {
    $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
}

$result = Await-WinRt ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
$result.Text
