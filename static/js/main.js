// Ana JavaScript dosyası

// Sayfa yüklendiğinde çalışacak kodlar
document.addEventListener('DOMContentLoaded', function() {
    // Bootstrap tooltip'leri etkinleştir
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Sayfa yüklendiğinde flash mesajlarını otomatik kapat
    setTimeout(function() {
        $('.alert-dismissible').alert('close');
    }, 5000);
});

// Para birimi formatı
function formatCurrency(value, currency = 'USDT', decimals = 2) {
    return parseFloat(value).toFixed(decimals) + ' ' + currency;
}

// Yüzde formatı
function formatPercent(value, decimals = 2) {
    return parseFloat(value).toFixed(decimals) + '%';
}

// Tarih formatı
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

// AJAX hata işleme
function handleAjaxError(error) {
    console.error('AJAX hatası:', error);
    let errorMessage = 'Bilinmeyen bir hata oluştu.';
    
    if (error.responseJSON && error.responseJSON.error) {
        errorMessage = error.responseJSON.error;
    } else if (error.statusText) {
        errorMessage = error.statusText;
    }
    
    // Hata mesajını göster
    const alertHtml = `
        <div class="alert alert-danger alert-dismissible fade show" role="alert">
            <i class="fas fa-exclamation-triangle"></i> ${errorMessage}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    
    // Eğer #alerts elementi varsa, içine ekle
    if (document.getElementById('alerts')) {
        document.getElementById('alerts').innerHTML = alertHtml;
    } else {
        // Yoksa sayfanın üstüne ekle
        const container = document.querySelector('.container-fluid');
        if (container) {
            const alertDiv = document.createElement('div');
            alertDiv.id = 'alerts';
            alertDiv.innerHTML = alertHtml;
            container.prepend(alertDiv);
        }
    }
}
