from django.shortcuts import render, redirect

def home_view(request):
    if request.user.is_authenticated:
        return render(request, 'home_page.html', {'username': request.user.username})
    else:
        return redirect('login')
    
def download_view(request):
    if request.user.is_authenticated:
        return render(request, 'download_page.html', {'username': request.user.username})
    else:
        return redirect('login')
