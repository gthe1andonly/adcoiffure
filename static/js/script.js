// JavaScript code to implement slideshow functionality
document.addEventListener("DOMContentLoaded", function() {
    let slides = document.querySelectorAll(".slide");
    let currentSlide = 0;

    // Function to show next slide
    function showSlide(index) {
        // Hide all slides
        slides.forEach(function(slide) {
            slide.classList.remove("active");
        });

        // Show the slide at the given index
        slides[index].classList.add("active");
    }

    // Initial slide display
    showSlide(currentSlide);

    // Function to navigate to next slide
    function nextSlide() {
        currentSlide = (currentSlide + 1) % slides.length;
        showSlide(currentSlide);
    }

    // Function to navigate to previous slide
    function prevSlide() {
        currentSlide = (currentSlide - 1 + slides.length) % slides.length;
        showSlide(currentSlide);
    }

    // Add event listeners for next and previous buttons
    document.querySelector("#nextBtn").addEventListener("click", nextSlide);
    document.querySelector("#prevBtn").addEventListener("click", prevSlide);
});