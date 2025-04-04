document.addEventListener('DOMContentLoaded',function(){const loadMoreButton=document.getElementById('load-more');const galleryContainer=document.querySelector('.row.g-4');const noMoreGalleries=document.getElementById('no-more-galleries');if(loadMoreButton){loadMoreButton.addEventListener('click',function(){const offset=parseInt(this.getAttribute('data-offset'));const url=this.getAttribute('data-url');const urlParams=new URLSearchParams(window.location.search);urlParams.set('offset',offset);const fetchUrl=`${url}?${urlParams.toString()}`;fetch(fetchUrl,{method:'GET',headers:{'X-Requested-With':'XMLHttpRequest',},}).then(response=>response.json()).then(data=>{if(data.error){console.error('خطا:',data.error);return;}
data.galleries.forEach(gallery=>{const galleryHtml=createGalleryItem(gallery);galleryContainer.insertAdjacentHTML('beforeend',galleryHtml);});const newOffset=offset+data.galleries.length;loadMoreButton.setAttribute('data-offset',newOffset);if(!data.has_more){loadMoreButton.style.display='none';noMoreGalleries.style.display='block';}
initializeSwipers();initializeBootstrapEvents();}).catch(error=>console.error('خطا در لود گالری‌ها:',error));});}
initializeSwipers();initializeBootstrapEvents();});function createGalleryItem(gallery){let imagesHtml='';gallery.image.forEach(imgUrl=>{imagesHtml+=`
            <div class="swiper-slide">
                <div class="image-box">
                    <img src="${imgUrl}" alt="تصویر" class="img-fluid" loading="lazy">
                </div>
            </div>
        `;});let dropdownHtml='';let modalHtml='';if(gallery.can_edit){dropdownHtml=`
            <div class="gallery-header mb-2 position-relative">
                <div class="dropdown position-absolute" style="top: 0; right: 0;">
                    <button class="btn btn-link p-0" type="button" 
                            data-bs-toggle="dropdown" aria-expanded="false">
                        <i class="fas fa-ellipsis-v"></i>
                    </button>
                    <ul class="dropdown-menu dropdown-menu-end" style="border-radius: 8px; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);">
                        <li>
                            <a class="dropdown-item" 
                               href="/gallery/update/${gallery.id}/" 
                               style="color: #495057; padding: 10px 15px; display: flex; align-items: center; transition: background-color 0.2s;"
                               onmouseover="this.style.backgroundColor='#e9ecef'" 
                               onmouseout="this.style.backgroundColor=''">
                                <i class="fas fa-edit me-2" style="color: #007bff;"></i> ویرایش
                            </a>
                        </li>
                        <li>
                            <button class="dropdown-item text-danger" 
                                    data-bs-toggle="modal" 
                                    data-bs-target="#deleteModal-${gallery.id}"
                                    style="padding: 10px 15px; display: flex; align-items: center; transition: background-color 0.2s;"
                                    onmouseover="this.style.backgroundColor='#f8d7da'" 
                                    onmouseout="this.style.backgroundColor=''">
                                <i class="fas fa-trash me-2" style="color: #dc3545;"></i> حذف
                            </button>
                        </li>
                    </ul>
                </div>
            </div>
        `;modalHtml=`
            <div class="modal fade" id="deleteModal-${gallery.id}" tabindex="-1" aria-labelledby="deleteModalLabel-${gallery.id}" aria-hidden="true">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content" style="border-radius: 10px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);">
                        <div class="modal-header" style="background-color: #f8d7da; border-bottom: 1px solid #f5c6cb;">
                            <h5 class="modal-title" id="deleteModalLabel-${gallery.id}" style="color: #721c24; font-weight: bold;">تأیید حذف</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="بستن"></button>
                        </div>
                        <div class="modal-body" style="font-size: 1.1rem; color: #333; padding: 20px;">
                            آیا مطمئن هستید که می‌خواهید این گالری را حذف کنید؟
                        </div>
                        <div class="modal-footer" style="border-top: 1px solid #e9ecef; padding: 15px;">
                            <form method="post" action="/gallery/delete/${gallery.id}/">
                                <input type="hidden" name="csrfmiddlewaretoken" value="${getCsrfToken()}">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal" 
                                        style="border-radius: 5px; padding: 8px 20px;">لغو</button>
                                <button type="submit" class="btn btn-danger" 
                                        style="border-radius: 5px; padding: 8px 20px;">تأیید</button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        `;}
return`
        <div class="col-md-6 col-sm-12">
            <div class="gallery-box position-relative overflow-hidden p-3">
                ${dropdownHtml}
                <div class="swiper-container gallery-swiper">
                    <div class="swiper-wrapper">
                        ${imagesHtml}
                    </div>
                    <div class="swiper-button-next"></div>
                    <div class="swiper-button-prev"></div>
                </div>
            </div>
        </div>
        ${modalHtml}
    `;}
function initializeSwipers(){const swiperContainers=document.querySelectorAll('.gallery-swiper');swiperContainers.forEach(container=>{if(!container.swiper){new Swiper(container,{slidesPerView:1,spaceBetween:10,navigation:{nextEl:'.swiper-button-next',prevEl:'.swiper-button-prev',},loop:true,});}});}
function initializeBootstrapEvents(){document.querySelectorAll('.dropdown-toggle').forEach(dropdown=>{if(!dropdown._dropdown){new bootstrap.Dropdown(dropdown);}});document.querySelectorAll('.modal').forEach(modal=>{if(!modal._modal){new bootstrap.Modal(modal);}});}
function getCsrfToken(){const csrfInput=document.querySelector('input[name="csrfmiddlewaretoken"]');return csrfInput?csrfInput.value:'';};